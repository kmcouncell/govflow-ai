import * as React from "react";
import { useNavigate } from "react-router-dom";

/** Client redirect so unknown paths do not overlap the home route in the outlet tree. */
export function RedirectToHome() {
  const navigate = useNavigate();
  React.useLayoutEffect(() => {
    navigate("/", { replace: true });
  }, [navigate]);
  return (
    <div className="p-6 text-sm text-muted-foreground" role="status">
      Redirecting to dashboard…
    </div>
  );
}
