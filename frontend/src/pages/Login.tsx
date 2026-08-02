import React from "react";
import {
  Box,
  Button,
  Container,
  Stack,
  Typography,
  Paper,
} from "@mui/material";
import LockIcon from "@mui/icons-material/Lock";
import { api } from "@/hooks/useApi";

export function Login(): React.ReactElement {
  const handleLogin = async () => {
    try {
      const response = await api.post("/auth/login");
      const token = response.data?.token;
      if (!token) {
        throw new Error("Login failed – no token returned");
      }
      localStorage.setItem("lifeguard_auth_token", token);
      window.location.href = "/patients/new";
    } catch (error) {
      alert("Login failed: " + (error as Error).message);
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
            Sign in via corporate SSO. All PHI is encrypted in your browser
            session and never leaves the trust boundary.
          </Typography>
          <Box sx={{ mt: 4 }}>
            <Button variant="contained" size="large" onClick={handleLogin}>
              Sign in
            </Button>
          </Box>
        </Stack>
      </Paper>
    </Container>
  );
}
