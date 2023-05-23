self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('smeApp-cache').then((cache) => {
      return cache.addAll([
        '/',
        '/static/css/main.css',
        '/static/js/main.js',
        '/static/assets/img/logo.png',
        '/static/assets/img/favicons/apple-touch-icon.png',
        '/static/assets/img/favicons/favicon-32x32.png',
        '/static/assets/img/favicons/favicon-16x16.png',
        '/static/assets/img/favicons/favicon.ico',
        '/static/assets/img/favicons/manifest.json',
        '/static/assets/img/favicons/mstile-150x150.png',
        '/static/vendors/imagesloaded/imagesloaded.pkgd.min.js',
        '/static/vendors/simplebar/simplebar.min.js',
        '/static/assets/js/config.js',
        '/static/vendors/simplebar/simplebar.min.css',
        '/static/assets/css/theme-rtl.min.css',
        '/static/assets/css/theme.min.css',
        '/static/assets/css/user-rtl.min.css',
        '/static/assets/css/user.min.css',
        '/static/vendors/popper/popper.min.js',
        '/static/vendors/bootstrap/bootstrap.min.js',
        '/static/vendors/anchorjs/anchor.min.js',
        '/static/vendors/is/is.min.js',
        '/static/vendors/fontawesome/all.min.js',
        '/static/vendors/lodash/lodash.min.js',
        '/static/vendors/list.js/list.min.js',
        '/static/vendors/feather-icons/feather.min.js',
        '/static/vendors/dayjs/dayjs.min.js',
        '/static/assets/js/phoenix.js',
        '/static/vendors/echarts/echarts.min.js',
        '/static/assets/js/ecommerce-dashboard.js'
      ]);
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      if (response) {
        return response;
      }

      return fetch(event.request).then(
        (response) => {
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          const responseToCache = response.clone();

          caches.open('smeApp-cache')
            .then((cache) => {
              cache.put(event.request, responseToCache);
            });

          return response;
        }
      );
    })
  );
});
