importScripts('/static/js/dexie.js');
const VERSION = '15062020';
const PRECACHE = `precache-v${VERSION}`;
const RUNTIME = `runtime-v${VERSION}`;
const MAXAGE = 10 * 60 * 1000; // 10min - living time of prediction responses

// IndexDB initializing
var db = new Dexie('predictions');
db.version(1).stores({
  predictions: 'key,response,timestamp',
});

// A list of local resources we always want to be cached.
const PRECACHE_URLS = [
  // 'index.html',
  //'/', // Alias for index.html
  '../static/css/main.css',
  '../static/css/main_index.css',
  '../static/css/topics.css',
  '../static/css/about.css',
  '../static/css/bootstrap.min.css',
  //'../static/js/main.js',
  '../static/js/dexie.js',
  '../static/js/jquery-3.4.1.min.js',
  '../static/js/bootstrap.min.js',
  '../static/js/popper.min.js',
];

// The install handler takes care of precaching the resources we always need.
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(PRECACHE)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      //.then(self.skipWaiting())
      .catch((e) => console.log(`SW installation error = ${e}`))
  );
});

// The activate handler takes care of cleaning up old caches.
self.addEventListener('activate', (event) => {
  const currentCaches = [PRECACHE, RUNTIME];
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) => {
        return cacheNames.filter((cacheName) => !currentCaches.includes(cacheName));
      })
      .then((cachesToDelete) => {
        return Promise.all(
          cachesToDelete.map((cacheToDelete) => {
              //console.log(`cacheToDelete: ${cacheToDelete}`);
            return caches.delete(cacheToDelete);
          })
        );
      })
      .then(() => self.clients.claim())
  );
});

// The fetch handler serves responses for resources from a cache.
// If no response is found, it populates the runtime cache with the response
// from the network before returning it to the page.
self.addEventListener('fetch', (event) => {
  // Cache same-origin requests: images, pages etc. Disabled for now cause
  // dynamic pages are used.
  if (event.request.url.startsWith(self.location.origin)) {
    // event.respondWith(
    //   caches.match(event.request).then((cachedResponse) => {
    //     if (cachedResponse) {
    //       return cachedResponse;
    //     }
    //     return caches.open(RUNTIME).then((cache) => {
    //       return fetch(event.request).then((response) => {
    //         // Put a copy of the response in the runtime cache.
    //         return cache.put(event.request, response.clone()).then(() => {
    //           return response;
    //         });
    //       });
    //     });
    //   })
    // );
  } else {
    // if not the same origin (Requesting lambda)
    if (event.request.method == 'POST') {
      event.respondWith(
        cacheMatch(event.request, db.predictions).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          return fetch(event.request.clone()).then((response) => {
            return cachePut(event.request.clone(), response.clone(), db.predictions).then(() => {
              return response;
            });
          });
        })
      );
    }
  }
});

function cachePut(request, response, store) {
  var key;
  return getPostId(request.clone())
    .then((id) => {
      key = id;
      return serializeResponse(response.clone());
    })
    .then((serializedResponse) => {
      return store.put({
        key: key,
        response: serializedResponse,
        timestamp: Date.now(),
      });
    });
}

function cacheMatch(request, store) {
  return getPostId(request.clone())
    .then((id) => {
      return store.get(id);
    })
    .then(function (data) {
      if (data) {
        // deleting records older then MAXAGE
        store.where('timestamp').below(Date.now() - MAXAGE).delete();
        // deserializing response
        return Promise.resolve(new Response(data.response.body, data.response));
      } else {
        return null;
        //throw Error('No such key!');
        // return new Response('', { status: 503, statusText: 'Service Unavailable' });
      }
    });
}

function getPostId(request) {
  return request
    .clone()
    .text()
    .then((body) => MD5(JSON.stringify(body)));
}

function serializeResponse(response) {
  let serialized = {
    headers: serializeHeaders(response.headers),
    status: response.status,
    statusText: response.statusText,
  };
  return response
    .clone()
    .text()
    .then(function (body) {
      serialized.body = body;
      return Promise.resolve(serialized);
    });
}

function serializeHeaders(h) {
  let headers = [];
  let headerNames = h.keys();
  for (let i = 0; i < headerNames.length; i++) {
    let headerName = headerNames[i];
    headers[headerName] = headers.get(headerName);
    console.log(`header: ${headers[headerName]}`);
  }
  return headers;
}

function clearOldData(store) {
  store.where('timestamp').below(Date.now() - MAXAGE).delete()
}

//MD5 hashing
var MD5 = function (d) {
  d = unescape(encodeURIComponent(d));
  result = M(V(Y(X(d), 8 * d.length)));
  return result.toLowerCase();
};

function M(d) {
  for (var _, m = '0123456789ABCDEF', f = '', r = 0; r < d.length; r++)
    (_ = d.charCodeAt(r)), (f += m.charAt((_ >>> 4) & 15) + m.charAt(15 & _));
  return f;
}

function X(d) {
  for (var _ = Array(d.length >> 2), m = 0; m < _.length; m++) _[m] = 0;
  for (m = 0; m < 8 * d.length; m += 8) _[m >> 5] |= (255 & d.charCodeAt(m / 8)) << m % 32;
  return _;
}

function V(d) {
  for (var _ = '', m = 0; m < 32 * d.length; m += 8) _ += String.fromCharCode((d[m >> 5] >>> m % 32) & 255);
  return _;
}

function Y(d, _) {
  (d[_ >> 5] |= 128 << _ % 32), (d[14 + (((_ + 64) >>> 9) << 4)] = _);
  for (var m = 1732584193, f = -271733879, r = -1732584194, i = 271733878, n = 0; n < d.length; n += 16) {
    var h = m,
      t = f,
      g = r,
      e = i;
    (f = md5_ii(
      (f = md5_ii(
        (f = md5_ii(
          (f = md5_ii(
            (f = md5_hh(
              (f = md5_hh(
                (f = md5_hh(
                  (f = md5_hh(
                    (f = md5_gg(
                      (f = md5_gg(
                        (f = md5_gg(
                          (f = md5_gg(
                            (f = md5_ff(
                              (f = md5_ff(
                                (f = md5_ff(
                                  (f = md5_ff(
                                    f,
                                    (r = md5_ff(
                                      r,
                                      (i = md5_ff(
                                        i,
                                        (m = md5_ff(m, f, r, i, d[n + 0], 7, -680876936)),
                                        f,
                                        r,
                                        d[n + 1],
                                        12,
                                        -389564586
                                      )),
                                      m,
                                      f,
                                      d[n + 2],
                                      17,
                                      606105819
                                    )),
                                    i,
                                    m,
                                    d[n + 3],
                                    22,
                                    -1044525330
                                  )),
                                  (r = md5_ff(
                                    r,
                                    (i = md5_ff(
                                      i,
                                      (m = md5_ff(m, f, r, i, d[n + 4], 7, -176418897)),
                                      f,
                                      r,
                                      d[n + 5],
                                      12,
                                      1200080426
                                    )),
                                    m,
                                    f,
                                    d[n + 6],
                                    17,
                                    -1473231341
                                  )),
                                  i,
                                  m,
                                  d[n + 7],
                                  22,
                                  -45705983
                                )),
                                (r = md5_ff(
                                  r,
                                  (i = md5_ff(
                                    i,
                                    (m = md5_ff(m, f, r, i, d[n + 8], 7, 1770035416)),
                                    f,
                                    r,
                                    d[n + 9],
                                    12,
                                    -1958414417
                                  )),
                                  m,
                                  f,
                                  d[n + 10],
                                  17,
                                  -42063
                                )),
                                i,
                                m,
                                d[n + 11],
                                22,
                                -1990404162
                              )),
                              (r = md5_ff(
                                r,
                                (i = md5_ff(
                                  i,
                                  (m = md5_ff(m, f, r, i, d[n + 12], 7, 1804603682)),
                                  f,
                                  r,
                                  d[n + 13],
                                  12,
                                  -40341101
                                )),
                                m,
                                f,
                                d[n + 14],
                                17,
                                -1502002290
                              )),
                              i,
                              m,
                              d[n + 15],
                              22,
                              1236535329
                            )),
                            (r = md5_gg(
                              r,
                              (i = md5_gg(
                                i,
                                (m = md5_gg(m, f, r, i, d[n + 1], 5, -165796510)),
                                f,
                                r,
                                d[n + 6],
                                9,
                                -1069501632
                              )),
                              m,
                              f,
                              d[n + 11],
                              14,
                              643717713
                            )),
                            i,
                            m,
                            d[n + 0],
                            20,
                            -373897302
                          )),
                          (r = md5_gg(
                            r,
                            (i = md5_gg(
                              i,
                              (m = md5_gg(m, f, r, i, d[n + 5], 5, -701558691)),
                              f,
                              r,
                              d[n + 10],
                              9,
                              38016083
                            )),
                            m,
                            f,
                            d[n + 15],
                            14,
                            -660478335
                          )),
                          i,
                          m,
                          d[n + 4],
                          20,
                          -405537848
                        )),
                        (r = md5_gg(
                          r,
                          (i = md5_gg(
                            i,
                            (m = md5_gg(m, f, r, i, d[n + 9], 5, 568446438)),
                            f,
                            r,
                            d[n + 14],
                            9,
                            -1019803690
                          )),
                          m,
                          f,
                          d[n + 3],
                          14,
                          -187363961
                        )),
                        i,
                        m,
                        d[n + 8],
                        20,
                        1163531501
                      )),
                      (r = md5_gg(
                        r,
                        (i = md5_gg(
                          i,
                          (m = md5_gg(m, f, r, i, d[n + 13], 5, -1444681467)),
                          f,
                          r,
                          d[n + 2],
                          9,
                          -51403784
                        )),
                        m,
                        f,
                        d[n + 7],
                        14,
                        1735328473
                      )),
                      i,
                      m,
                      d[n + 12],
                      20,
                      -1926607734
                    )),
                    (r = md5_hh(
                      r,
                      (i = md5_hh(i, (m = md5_hh(m, f, r, i, d[n + 5], 4, -378558)), f, r, d[n + 8], 11, -2022574463)),
                      m,
                      f,
                      d[n + 11],
                      16,
                      1839030562
                    )),
                    i,
                    m,
                    d[n + 14],
                    23,
                    -35309556
                  )),
                  (r = md5_hh(
                    r,
                    (i = md5_hh(i, (m = md5_hh(m, f, r, i, d[n + 1], 4, -1530992060)), f, r, d[n + 4], 11, 1272893353)),
                    m,
                    f,
                    d[n + 7],
                    16,
                    -155497632
                  )),
                  i,
                  m,
                  d[n + 10],
                  23,
                  -1094730640
                )),
                (r = md5_hh(
                  r,
                  (i = md5_hh(i, (m = md5_hh(m, f, r, i, d[n + 13], 4, 681279174)), f, r, d[n + 0], 11, -358537222)),
                  m,
                  f,
                  d[n + 3],
                  16,
                  -722521979
                )),
                i,
                m,
                d[n + 6],
                23,
                76029189
              )),
              (r = md5_hh(
                r,
                (i = md5_hh(i, (m = md5_hh(m, f, r, i, d[n + 9], 4, -640364487)), f, r, d[n + 12], 11, -421815835)),
                m,
                f,
                d[n + 15],
                16,
                530742520
              )),
              i,
              m,
              d[n + 2],
              23,
              -995338651
            )),
            (r = md5_ii(
              r,
              (i = md5_ii(i, (m = md5_ii(m, f, r, i, d[n + 0], 6, -198630844)), f, r, d[n + 7], 10, 1126891415)),
              m,
              f,
              d[n + 14],
              15,
              -1416354905
            )),
            i,
            m,
            d[n + 5],
            21,
            -57434055
          )),
          (r = md5_ii(
            r,
            (i = md5_ii(i, (m = md5_ii(m, f, r, i, d[n + 12], 6, 1700485571)), f, r, d[n + 3], 10, -1894986606)),
            m,
            f,
            d[n + 10],
            15,
            -1051523
          )),
          i,
          m,
          d[n + 1],
          21,
          -2054922799
        )),
        (r = md5_ii(
          r,
          (i = md5_ii(i, (m = md5_ii(m, f, r, i, d[n + 8], 6, 1873313359)), f, r, d[n + 15], 10, -30611744)),
          m,
          f,
          d[n + 6],
          15,
          -1560198380
        )),
        i,
        m,
        d[n + 13],
        21,
        1309151649
      )),
      (r = md5_ii(
        r,
        (i = md5_ii(i, (m = md5_ii(m, f, r, i, d[n + 4], 6, -145523070)), f, r, d[n + 11], 10, -1120210379)),
        m,
        f,
        d[n + 2],
        15,
        718787259
      )),
      i,
      m,
      d[n + 9],
      21,
      -343485551
    )),
      (m = safe_add(m, h)),
      (f = safe_add(f, t)),
      (r = safe_add(r, g)),
      (i = safe_add(i, e));
  }
  return Array(m, f, r, i);
}

function md5_cmn(d, _, m, f, r, i) {
  return safe_add(bit_rol(safe_add(safe_add(_, d), safe_add(f, i)), r), m);
}

function md5_ff(d, _, m, f, r, i, n) {
  return md5_cmn((_ & m) | (~_ & f), d, _, r, i, n);
}

function md5_gg(d, _, m, f, r, i, n) {
  return md5_cmn((_ & f) | (m & ~f), d, _, r, i, n);
}

function md5_hh(d, _, m, f, r, i, n) {
  return md5_cmn(_ ^ m ^ f, d, _, r, i, n);
}

function md5_ii(d, _, m, f, r, i, n) {
  return md5_cmn(m ^ (_ | ~f), d, _, r, i, n);
}

function safe_add(d, _) {
  var m = (65535 & d) + (65535 & _);
  return (((d >> 16) + (_ >> 16) + (m >> 16)) << 16) | (65535 & m);
}

function bit_rol(d, _) {
  return (d << _) | (d >>> (32 - _));
}
