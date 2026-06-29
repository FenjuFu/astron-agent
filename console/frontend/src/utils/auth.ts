import { performLogout, casdoorSdk } from '@/config/casdoor';
import { buildAppUrl, getAppPathname } from '@/utils/base-path';

export const handleLoginRedirect = (): void => {
  sessionStorage.setItem(
    'postLoginRedirect',
    getAppPathname() + window.location.search
  );
  casdoorSdk.signin_redirect();
};

export const handleLogout = (): void => {
  performLogout(buildAppUrl('/home'));
};
