// SoloNest Background Service Worker for Web Push & Closed-Tab Notifications
self.addEventListener('install', function(event) {
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  event.waitUntil(self.clients.claim());
});

// Handle Web Push Event sent from Server even when browser tab is closed
self.addEventListener('push', function(event) {
  var data = { title: 'SoloNest Booking Alert', body: 'New booking request received for your room!' };
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data.body = event.data.text();
    }
  }

  var options = {
    body: data.body || 'A guest requested a booking for your property.',
    icon: '/static/images/logo-icon.png',
    data: { url: data.link || '/dashboard/' },
    requireInteraction: true
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'SoloNest Booking Alert', options)
  );
});

// Handle user clicking the OS notification when tab is closed
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  var targetUrl = (event.notification.data && event.notification.data.url) ? event.notification.data.url : '/dashboard/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
      for (var i = 0; i < clientList.length; i++) {
        var client = clientList[i];
        if ('focus' in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
