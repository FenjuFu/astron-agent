const ensureLeadingSlash = (value: string): string => {
  if (!value) return '/';
  return value.startsWith('/') ? value : `/${value}`;
};

const stripTrailingSlash = (value: string): string => {
  if (!value || value === '/') return '/';
  return value.replace(/\/+$/, '') || '/';
};

const normalizePath = (value: string): string => {
  const withLeadingSlash = ensureLeadingSlash(value);
  return stripTrailingSlash(withLeadingSlash);
};

const normalizeBasePath = (value?: string): string => {
  if (!value || value === '/') return '';
  return normalizePath(value);
};

export const appBasePath = normalizeBasePath(import.meta.env.BASE_URL);

export const getAppBasePath = (): string => appBasePath;

export const withAppBasePath = (path = '/'): string => {
  const normalizedPath = normalizePath(path);
  if (!appBasePath) {
    return normalizedPath;
  }
  if (
    normalizedPath === appBasePath ||
    normalizedPath.startsWith(`${appBasePath}/`)
  ) {
    return normalizedPath;
  }
  return normalizedPath === '/'
    ? `${appBasePath}/`
    : `${appBasePath}${normalizedPath}`;
};

export const stripAppBasePath = (pathname: string): string => {
  const normalizedPathname = normalizePath(pathname);
  if (!appBasePath) {
    return normalizedPathname;
  }
  if (normalizedPathname === appBasePath) {
    return '/';
  }
  if (normalizedPathname.startsWith(`${appBasePath}/`)) {
    return normalizedPathname.slice(appBasePath.length) || '/';
  }
  return normalizedPathname;
};

export const getAppPathname = (): string =>
  stripAppBasePath(window.location.pathname);

export const buildAppUrl = (path = '/'): string =>
  `${window.location.origin}${withAppBasePath(path)}`;
