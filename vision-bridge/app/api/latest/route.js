import { head } from '@vercel/blob';

export async function GET() {
  try {
    const b = await head('latest-frame.png');
    return Response.redirect(b.url, {
      status: 302,
      headers: {
        'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
  } catch (e) {
    return Response.json(
      { error: 'no frame yet' },
      {
        status: 404,
        headers: { 'Cache-Control': 'no-store' }
      }
    );
  }
}
