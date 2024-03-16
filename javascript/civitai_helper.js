'use strict'

async function notice(options) {
    if (!'Notification' in window) {
        console.warn('Notifications are not supported')
    } else {
        function _notice() { 
            let n = new Notification('Stable Diffusion', options) 
            if (options.time)  {
                setTimeout(() => n.close(), options.time * 1000)
            }
            return n
        }
        if (Notification.permission === 'granted') {
            _notice()
        } else {
            let permission = await Notification.requestPermission()
            if (permission === 'granted') {
                _notice()
            }
        }
    }
}

// send msg to python side by filling a hidden text box
// then will click a button to trigger an action
// msg is an object, not a string, will be stringify in this function
function send_ch_py_msg(id, msg) {
    // Get hidden components of extension
    let btn = _(id)
    if (!btn) return

    // Fill the message box
    let js_msg_txtbox = $('#ch_js_msg_txtbox textarea')
    if (js_msg_txtbox && msg) {
        js_msg_txtbox.value = JSON.stringify(msg)
        updateInput(js_msg_txtbox)
    }

    // Click the hidden button
    btn.click()
}

// get msg from python side from a hidden textbox
// normally this is an old msg, need to wait for a new msg
function get_ch_py_msg() {
    return $('#ch_py_msg_txtbox textarea')?.value
}

// get msg from python side from a hidden textbox
// it will try once in every sencond, until it reach the max try times
function get_new_ch_py_msg(max_count = 9) {
    return new Promise((resolve, reject) => {
        let msgbox = $('#ch_py_msg_txtbox textarea'), count = 0
        function check() {
            let new_msg = msgbox?.value
            if (new_msg) {
                updateInput(msgbox, '') // clear msg in both sides (client & server)
                resolve(new_msg)
            } else if (++count < max_count) {
                setTimeout(check, 111)
            } else {
                reject('max retry exceeded')
            }
        }
        check()
    })
}

function getActivePrompt(neg) {
    let tab = uiCurrentTab
    if (neg) tab += '_neg'
    return get_uiCurrentTabContent().one(`#${tab}_prompt textarea`)
}

// button's click function
async function open_model_url(evt, model_type, search_term) {
    evt.stopPropagation()
    try {
        send_ch_py_msg('ch_js_action_btn', {
            action: 'open_model_url',
            search_term,
            model_type
        })
        let new_py_msg = await get_new_ch_py_msg()
        if (new_py_msg) {
            let {url, open_url_with_js} = JSON.parse(new_py_msg)
            if (url) {
                let el = evt.target
                el.href = url
                el.target = '_blank'
                el.removeAttribute("onclick")
                if (open_url_with_js) {
                    open(url, '_blank')
                }
            }
        }
    } catch (e) {
        console.error(e)
    }
}

async function open_model_folder(evt, model_type, search_term) {
    evt.stopPropagation()
    send_ch_py_msg('ch_js_action_btn', {
        action: 'open_model_folder',
        model_filepath: evt.target.closest('.card').dataset.sortPath,
        model_type,
        search_term
    })
}

async function delete_model(evt, model_type, search_term) {
    evt.stopPropagation()
    if (!confirm(`Confirm delete: \n${search_term} ??`)) return

    let card = evt.target.closest('.card')
    let cover = card.firstElementChild.src
    new Image().src = cover

    send_ch_py_msg('ch_js_action_btn', {
        'action': 'delete_model',
        'model_type': model_type,
        'search_term': search_term
    })
    // Check response msg from python
    let new_py_msg = await get_new_ch_py_msg()
    if (new_py_msg) {
        notice({
            body: `Model deleted: ${search_term.substr(1)}`,
            image: cover,
            icon: cover,
            time: 5
        })
        evt.target.closest('.card').remove()
    }
}

function add_trigger_words(event, model_type, search_term) {
    send_ch_py_msg('ch_js_add_trigger_words_btn', {
        'action': 'add_trigger_words',
        'model_type': model_type,
        'search_term': search_term,
        'prompt': getActivePrompt().value,
        'neg_prompt': ''
    })
    event.stopPropagation()
    event.preventDefault()
}

function use_preview_prompt(event, model_type, search_term) {
    send_ch_py_msg('ch_js_use_preview_prompt_btn', {
        'action': 'use_preview_prompt',
        'model_type': model_type,
        'search_term': search_term,
        'prompt': getActivePrompt().value,
        'neg_prompt': getActivePrompt(1).value
    })
    event.stopPropagation()
    event.preventDefault()
}

// download model's new version into SD at python side
function ch_dl_model_new_version(event, model_path, version_id, download_url) {
    // must confirm before downloading
    if (!confirm('Confirm to download.\n\nCheck Download Model Section\'s log and console log for detail.')) return

    send_ch_py_msg('ch_js_dl_model_new_version_btn', {
        action: 'dl_model_new_version',
        model_path: model_path,
        version_id: version_id,
        download_url: download_url
    })
    event.stopPropagation()
    event.preventDefault()
}

// fast pasete civitai model url and trigger model info loading
async function check_clipboard() {
    let text = await navigator.clipboard.readText()
    let el = $('#model_download_url_txt')
    let textarea = $('textarea', el)
    if (text.startsWith('https://civitai.com/models/')) {
        if (textarea.value == text) {
            let version = _('ch_dl_all_ckb').previousElementSibling.querySelector('input')
            if (version.value) {
                _('ch_download_btn')?.click()
            }
            return
        }
        updateInput(textarea, text)
    }
    textarea.value && $('button', el).click()
}

async function fetch_info() {
    let text = await navigator.clipboard.readText()
    let el = $('#ch_info_url')
    let textarea = $('textarea', el)
    updateInput(textarea, text)
    el.parentElement.nextElementSibling.click()
}

const model_type_mapping = {
    'textual_inversion': 'ti',
    'hypernetworks': 'hyper',
    'checkpoints': 'ckp',
    'lora': 'lora'
}

function listenToCardHover() {
    let pages = $$('.extra-page')
    if (pages.length == 0) {
        return setTimeout(listenToCardHover, 999)
    }
    for (let page of pages) {
        page.on('mouseover', e => {
            let el = e.target
            if (el.className == 'actions')  {
                let arr = el.closest('.gradio-html').id.split('_').slice(1, -1)
                let model_type = model_type_mapping[arr.join('_')]
                update_card(el, model_type)
            }
        })
    }
}

function update_card(card, model_type) {
    let additionalEl = card.querySelector('.additional')
    if (additionalEl.childElementCount >= 4) return

    let search_term = card.querySelector('.search_terms')?.innerText
    if (!search_term) return

    let args = `event, '${model_type}', '${search_term.replaceAll('\\', '\\\\')}'`
    let btns = [
        {innerHTML: '🌐', title: 'Open in Civitai', onclick: 'open_model_url(' + args + ')'},
        {innerHTML: '💡', title: 'Add trigger words to prompt', onclick: 'add_trigger_words(' + args + ')'},
        {innerHTML: '🪞', title: 'Use prompt from preview image', onclick: 'use_preview_prompt(' + args + ')'},
        {innerHTML: '📂', title: 'Open in Explorer', onclick: 'open_model_folder(' + args + ')'},
        {innerHTML: '🗑️', title: 'Delete model', onclick: 'delete_model(' + args + ')'}
    ]
    for (let btn of btns) {
        createElement('a','ch-action', btn, additionalEl)
    }
}

function addHelperBtn(tab_prefix) {
    let tab_nav = $(`#${tab_prefix}_extra_tabs > .tab-nav`)
    if (!tab_nav) {
        return setTimeout(addHelperBtn, 999, tab_prefix)
    }
    createElement('label', 'gradio-button tool ch-fetch', {
        title: 'Fetch missing model info and preview',
        innerText: '⇊' // 🖼️
    }, tab_nav).setAttribute('for', 'ch_scan_model_civitai_btn')
}


onUiLoaded(() => {
    ['txt2img', 'img2img'].forEach(addHelperBtn)
    listenToCardHover()
})

on('keydown', e => {
    if (isEditable(e.target) || uiCurrentTab != 'Civitai Helper') return
    switch (e.key) {
        case 'f': fetch_info()
            break
        case 'x': check_clipboard()
    }
})
