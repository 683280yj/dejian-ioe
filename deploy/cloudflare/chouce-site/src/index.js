const ORIGIN = 'https://cc.159-138-136-40.sslip.io';
const SYSTEM_ORIGIN = 'https://ioe.159-138-136-40.sslip.io';

export default {
  async fetch(request, env) {
    const incoming = new URL(request.url);
    if (incoming.pathname === '/api/bookings/') {
      if (request.method !== 'POST') {
        return new Response('Method Not Allowed', { status: 405, headers: { Allow: 'POST' } });
      }
      if (request.headers.get('Origin') !== incoming.origin ||
          !request.headers.get('Content-Type')?.toLowerCase().startsWith('application/json')) {
        return Response.json({ message: '预约请求来源有误' }, { status: 403 });
      }
      const body = await request.arrayBuffer();
      if (body.byteLength > 4096) {
        return Response.json({ message: '提交内容过长' }, { status: 413 });
      }
      if (!env.BOOKING_SUBMISSION_TOKEN) {
        return Response.json({ message: '预约服务暂不可用' }, { status: 503 });
      }
      const upstream = new URL('/api/public/bookings/', SYSTEM_ORIGIN);
      const response = await fetch(upstream, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Booking-Token': env.BOOKING_SUBMISSION_TOKEN,
        },
        body,
        redirect: 'manual',
      });
      return new Response(response.body, {
        status: response.status,
        headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
      });
    }
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      return new Response('Method Not Allowed', { status: 405, headers: { Allow: 'GET, HEAD' } });
    }

    const upstream = new URL(incoming.pathname + incoming.search, ORIGIN);
    const response = await fetch(new Request(upstream, request), { redirect: 'manual' });
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
