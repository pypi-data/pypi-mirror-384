function get_cookie(name) {
  const cookies = document.cookie.split(';')
  for (const cookie of cookies) {
    const [cookieName, cookieValue] = cookie.trim().split('=')
    if (cookieName === name) {
      return decodeURIComponent(cookieValue)
    }
  }
  return null
}
function delete_cookie(name) {
  document.cookie = name + `=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`
}

function set_cookies(cookies) {
  cookies = new Map(Object.entries(cookies))
  for (var [key, value] of cookies) {
    set_simple_cookie(key, value)
  }
}

function set_simple_cookie(key, value) {
  cookie_enabled = get_cookie('cookie_enabled')
  if (cookie_enabled != '1') {
    return
  }
  const expiryDate = new Date()
  expiryDate.setFullYear(expiryDate.getFullYear() + 20)
  document.cookie = `${key}=${value}; expires=${expiryDate.toUTCString()}; path=/`
}
function update_href(query) {
  query = new Map(Object.entries(query))
  const url = new URL(window.location.href)
  const params = new URLSearchParams(url.search)
  for (const [key, value] of query) {
    params.set(key, value)
  }
  url.search = params.toString()
  window.location.href = url.href
}
function open_small_window(url) {
  const size_times = 1 / 4
  const width = Math.round(screen.width * size_times)
  const height = Math.round(screen.height * size_times)
  const left = Math.round((screen.width - width) / 2)
  const top = Math.round((screen.height - height) / 2)
  const windowFeatures = `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
  window.open(url, '_blank', windowFeatures)
}

document.addEventListener('DOMContentLoaded', function () {
  if (!document.cookie.includes('cookie_enabled=1')) {
    document.getElementById('cookieConsent').style.display = 'block'
  }

  var accept_cookies_element = document.getElementById('acceptCookies')
  if (accept_cookies_element != undefined) {
    accept_cookies_element.addEventListener('click', function () {
      const expiryDate = new Date()
      expiryDate.setFullYear(expiryDate.getFullYear() + 20)
      document.cookie = `cookie_enabled=1; expires=${expiryDate.toUTCString()}; path=/`
      document.getElementById('cookieConsent').style.display = 'none'
    })
  }
  var reject_cookies_element = document.getElementById('rejectCookies')
  if (reject_cookies_element != undefined) {
    reject_cookies_element.addEventListener('click', function () {
      document.getElementById('cookieConsent').style.display = 'none'
    })
  }
})

function set_page_size() {
  const page_size = document.querySelector('#page_size').value
  set_simple_cookie('page_size', page_size)
  update_href({ per_page: page_size })
}

$(document).ready(function () {
  page_size_forms = $('[name="page_size"]')
  if (page_size_forms.length > 0) {
    page_size_forms.on('submit', function (event) {
      event.preventDefault()
      set_page_size()
    })
  }
})

function set_page(num) {
  update_href({ page: num })
}
