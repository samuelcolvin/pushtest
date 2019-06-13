self.addEventListener('install', e => {
  console.log('service worker installed', e)
})

self.addEventListener('message', e => {
  console.log('message', e)
  clients.matchAll().then(clients => console.log('clients:', clients))
})


self.addEventListener('push', event => {
  console.log('Received a push message', event)
  console.log('Event:', event.data.text())
  event.waitUntil(
    self.registration.showNotification('Yay a message.', {
      body: event.data.text(),
    })
  )
})
