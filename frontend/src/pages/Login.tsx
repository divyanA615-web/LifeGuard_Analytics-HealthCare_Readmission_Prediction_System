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

export function Login(): React.ReactElement {
  const handleLogin = () => {
    const endpoint = import.meta.env.VITE_API_BASE ?? "/v1";
    const next = encodeURIComponent(window.location.origin + "/patients/new");
    window.location.href = `${endpoint}/__auth/login?next=${next}`;
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
