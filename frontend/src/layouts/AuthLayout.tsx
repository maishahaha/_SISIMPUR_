import { Outlet } from "react-router-dom";
import Background from "@/components/layout/Background";

export default function AuthLayout() {
  return (
    <div className="min-h-screen flex items-center justify-center relative">
      <Background />
      <div className="relative z-10 w-full">
        <Outlet />
      </div>
    </div>
  );
}
