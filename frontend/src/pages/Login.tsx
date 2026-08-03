import React from "react";
import {
  Box,
  Button,
  Container,
  Stack,
  Typography,
  Paper,
  Alert,
} from "@mui/material";
import LockIcon from "@mui/icons-material/Lock";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "@/hooks/useApi";

export function Login(): React.ReactElement {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const handleLogin = async () => {
    setError(null);
    setLoading(true);
    try {
      const response = await api.post("/auth/login");
      const token: string | undefined = response.data?.token;
      if (!token) {
        throw new Error("Login failed – no token returned");
      }
      // Persist token for header-based auth; cookie set by backend too
      try {
        localStorage.setItem("lifeguard_auth_token", token);
      } catch {
        // storage blocked; cookie-based auth still works if CORS/withCredentials set
      }
      const next = searchParams.get("next") || "/patients/new";
      navigate(next, { replace: true });
    } catch (err) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || (err as Error).message;
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 12 }}>
      <Paper elevation={3} sx={{ p: 5 }}>
        <Stack spacing={3} alignItems="center">
          <LockIcon sx={{ fontSize: 60, color: "primary.main" }} />
          <Typography variant="h4" component="h1">
            LifeGuard
          </Typography>
          <Typography variant="subtitle2" color="text.secondary">
            Readmission Risk Prediction
          </Typography>
          <Typography variant="body2" textAlign="center" sx={{ mt: 2 }}>
            Development sign-in issues a scoped dev token. In production this
            flow must be replaced by SSO with MFA.
          </Typography>
          {error && (
            <Alert severity="error" sx={{ width: "100%" }}>
              {error}
            </Alert>
          )}
          <Box sx={{ mt: 4 }}>
            <Button
              variant="contained"
              size="large"
              onClick={handleLogin}
              disabled={loading}
            >
              {loading ? "Signing in…" : "Sign in"}
            </Button>
          </Box>
        </Stack>
      </Paper>
    </Container>
  );
}
