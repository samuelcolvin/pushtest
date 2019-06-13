const output = document.getElementById('output')
const message_el = document.getElementById('message')
output.innerText = 'running...'

window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js').then(initialiseState))

function initialiseState(r) {
  // console.log('ServiceWorker registration successful with scope: ', r.scope)
  r.onupdatefound = () => {
    const installing_worker = r.installing
    if (installing_worker !== null) {
      installing_worker.onstatechange = () => {
        if (installing_worker.state === 'installed' && navigator.serviceWorker.controller) {
          console.log('New content is available and will be used when all tabs for this page are closed.')
          output.innerText += 'New content, reload.'
        }
      }
    }
  }

  if (!('showNotification' in ServiceWorkerRegistration.prototype)) {
    console.warn('Notifications aren\'t supported.')
    return
  }

  console.log('Notification.permission:', Notification.permission)

  // Check if push messaging is supported
  if (!('PushManager' in window)) {
    console.warn('Push messaging isn\'t supported.')
    return
  }

  // We need the service worker registration to check for a subscription
  navigator.serviceWorker.ready.then(serviceWorkerRegistration => {
    // Do we already have a push message subscription?

    serviceWorkerRegistration.pushManager.getSubscription()
      .then(sub => {
        if (sub) {
          console.log('already subsribed, sub:', sub)
          output.innerText = 'existing subscription:\n' + JSON.stringify(sub.toJSON(), null, 2)
        } else {
          subscribe(serviceWorkerRegistration.pushManager)
        }

        navigator.serviceWorker.addEventListener('message', event => {
          console.log('got message: ', event)
          event.ports[0].postMessage(null)
          message_el.innerText = event.data
        })
      })
      .catch(err => console.warn('Error during getSubscription()', err))
  })
}

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4)
  const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/')
  const rawData = window.atob(base64)
  return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)))
}

function subscribe(manager) {
  const sub_options = {
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(
      'BIEDu10LOR8VN-i-kWMmrICdEMofTr0_EP_Ty4SkAmj-Oc6N6lhJpofzRmh87rcI_9JLamlDY-T3DRsOJciufJo'
    )
  }
  manager.subscribe(sub_options)
    .then(sub => {
      console.log('subscription successful, sub:', sub)
      output.innerText = 'new subscription:\n' + JSON.stringify(sub.toJSON(), null, 2)
    })
    .catch(e => {
      if (Notification.permission === 'denied') {
        // The user denied the notification permission which
        // means we failed to subscribe and the user will need
        // to manually change the notification permission to
        // subscribe to push messages
        console.warn('Permission for Notifications was denied')
      } else {
        // A problem occurred with the subscription common reasons
        // include network errors, and lacking gcm_sender_id and/or
        // gcm_user_visible_only in the manifest.
        console.error('Unable to subscribe to push.', e)
      }
    })
}
