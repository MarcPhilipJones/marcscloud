import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="page">
      <h1>Hello World</h1>
      <p>Welcome to the MJ Hello World Power Pages site.</p>
      <Link
        to="/cases"
        className="btn btn-primary"
        style={{ marginTop: "1rem" }}
      >
        View My Cases
      </Link>
    </div>
  );
}
