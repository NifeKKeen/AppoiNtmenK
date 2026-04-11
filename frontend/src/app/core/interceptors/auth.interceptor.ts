import { HttpInterceptorFn } from '@angular/common/http';

const PUBLIC_URLS = ['/api/register/', '/api/token/'];

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  // Don't attach tokens to public endpoints
  const isPublic = PUBLIC_URLS.some((url) => req.url.includes(url));
  if (isPublic) {
    return next(req);
  }

  const token = localStorage.getItem('access_token');
  if (token) {
    const cloned = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    });
    return next(cloned);
  }
  return next(req);
};
