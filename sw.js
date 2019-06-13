self.addEventListener('install', e => {
  console.log('service worker installed', e)
})

function push_to_client (client, msg) {
  return new Promise(resolve=> {
    const msg_chan = new MessageChannel()
    msg_chan.port1.onmessage = event => resolve(event.data)
    client.postMessage(msg, [msg_chan.port2])
  })
}

async function on_push (event) {
  console.log('Received a push message', event)
  const data = event.data.text()
  await self.registration.showNotification('new message', {
    body: data,
    icon: './image1.png',
    badge: './image2.png',
    // image: './image3.png',
    // vibrate: [200, 50, 100],
    // requireInteraction: true,
  })
  const clients = await self.clients.matchAll({type: 'window'})
  const promises = clients.map(client => push_to_client(client, data))
  await Promise.all(promises)
}
self.addEventListener('push', event => event.waitUntil(on_push(event)))

async function click (event) {
  console.log('On notification click: ', event)
  event.notification.close()

  // await self.clients.openWindow('/')
  // This looks to see if the current is already open and
  // focuses if it is
  const clients = await self.clients.matchAll({type: 'window'})
  for (let client of clients) {
    // console.log('client', client)
    // TODO check url
    if ('focus' in client) {
      await client.focus()
      return
    }
  }
  await self.clients.openWindow('/')
}
self.addEventListener('notificationclick', event => event.waitUntil(click(event)))
