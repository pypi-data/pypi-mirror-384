//Handling Viewports
const handleViewport = () => {
  let viewportWidth = window.innerWidth > 1024 ? window.innerWidth : 1024;
  if (window.location.pathname !== "/login") {
    document
      .querySelector('meta[name="viewport"]')
      .setAttribute("content", `width=${viewportWidth}, initial-scale=1`);
  }
};
window.addEventListener("resize", handleViewport);
handleViewport();

// Hotjar
(function (h, o, t, j, a, r) {
  h.hj =
    h.hj ||
    function () {
      (h.hj.q = h.hj.q || []).push(arguments);
    };
  h._hjSettings = { hjid: 3486723, hjsv: 6 };
  a = o.getElementsByTagName("head")[0];
  r = o.createElement("script");
  r.async = 1;
  r.src = t + h._hjSettings.hjid + j + h._hjSettings.hjsv;
  a.appendChild(r);
})(window, document, "https://static.hotjar.com/c/hotjar-", ".js?sv=");

// Google Tag Manager
window.dataLayer = window.dataLayer || [];
function gtag() {
  window.dataLayer.push(arguments);
}
gtag("js", new Date());

gtag("config", "G-SG3K4C5YR0");

// AWS RUM
(function (n, i, v, r, s, c, x, z) {
  x = window.AwsRumClient = { q: [], n: n, i: i, v: v, r: r, c: c };
  window[n] = function (c, p) {
    x.q.push({ c: c, p: p });
  };
  z = document.createElement("script");
  z.async = true;
  z.src = s;
  document.head.insertBefore(
    z,
    document.head.getElementsByTagName("script")[0]
  );
})(
  "cwr",
  "eba827cf-f3e4-4c90-b279-598a430c171e",
  "1.0.0",
  "us-east-2",
  "https://client.rum.us-east-1.amazonaws.com/1.13.6/cwr.js",
  {
    sessionSampleRate: 1,
    guestRoleArn:
      "arn:aws:iam::027730031917:role/RUM-Monitor-us-east-2-027730031917-1628058627861-Unauth",
    identityPoolId: "us-east-2:5e664df5-2810-4603-8d3d-f94833b91ff2",
    endpoint: "https://dataplane.rum.us-east-2.amazonaws.com",
    telemetries: [
      "performance",
      "errors",
      ["http", { recordAllRequests: true }],
    ],
    allowCookies: true,
    enableXRay: false,
  }
);
