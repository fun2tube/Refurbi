import { apiBaseUrl } from "@/lib/config";
import { LoginForm } from "./LoginForm";

export const dynamic = "force-dynamic";

export default function LoginPage() {
  return (
    <div className="max-w-sm space-y-4">
      <h1 className="font-display text-2xl font-bold">Admin sign in</h1>
      <LoginForm apiBase={apiBaseUrl()} />
    </div>
  );
}
