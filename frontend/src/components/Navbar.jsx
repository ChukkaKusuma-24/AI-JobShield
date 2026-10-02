import { NavLink, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const links = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/analyze', label: 'Analyze' },
  { to: '/ocr', label: 'OCR' },
  { to: '/company', label: 'Company' },
  { to: '/url', label: 'URL' },
  { to: '/reports', label: 'Reports' },
  { to: '/history', label: 'History' },
  { to: '/profile', label: 'Profile' },
  { to: '/about', label: 'About' },
];

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-40 border-b border-ink/10 bg-paper/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link to="/" className="font-display text-xl font-bold tracking-tight text-ink">
          AI <span className="text-accent">JobShield</span>
        </Link>
        {isAuthenticated ? (
          <nav className="hidden items-center gap-1 md:flex">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                className={({ isActive }) =>
                  `rounded-md px-2.5 py-1.5 text-sm font-medium transition ${
                    isActive ? 'bg-accent/15 text-accent' : 'text-ink/70 hover:bg-ink/5'
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
          </nav>
        ) : null}
        <div className="flex items-center gap-2">
          {isAuthenticated ? (
            <>
              <Link to="/profile" className="hidden text-sm text-ink/70 hover:text-accent sm:inline font-medium">
                {user?.name}
              </Link>
              <button type="button" className="btn-secondary !py-1.5" onClick={logout}>
                Logout
              </button>
            </>
          ) : (
            <Link to="/auth" className="btn-primary !py-1.5">
              Sign in
            </Link>
          )}
        </div>
      </div>
      {isAuthenticated ? (
        <div className="flex gap-1 overflow-x-auto border-t border-ink/5 px-4 py-2 md:hidden">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) =>
                `whitespace-nowrap rounded-md px-2 py-1 text-xs font-medium ${
                  isActive ? 'bg-accent/15 text-accent' : 'text-ink/70'
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </div>
      ) : null}
    </header>
  );
}
