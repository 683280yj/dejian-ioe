const ORIGIN = 'https://ioe.159-138-136-40.sslip.io';

export default {
  async fetch(request) {
    const incoming = new URL(request.url);
    const target = new URL(incoming.pathname + incoming.search, ORIGIN);
    const response = await fetch(new Request(target, request), { redirect: 'manual' });
    const headers = new Headers(response.headers);
    const location = headers.get('location');
    if (location) {
      const redirect = new URL(location, ORIGIN);
      if (redirect.origin === ORIGIN) {
        redirect.protocol = incoming.protocol;
        redirect.host = incoming.host;
        headers.set('location', redirect.toString());
      }
    }
    return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
  },
};
