import { NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <header className="nav">
      <div className="container nav-inner">
        <NavLink to="/" className="brand">🛒 AI Shopping Assistant</NavLink>
        <nav>
          <NavLink to="/" end>Home</NavLink>
          <NavLink to="/detect">Live Detection</NavLink>
        </nav>
      </div>
    </header>
  );
}
