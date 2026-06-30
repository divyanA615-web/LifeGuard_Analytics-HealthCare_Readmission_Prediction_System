import React from "react";
import {
  Container,
  Paper,
  Typography,
  Stack,
  Chip,
  Alert,
  Box,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { fetchModelInfo } from "@/hooks/useApi";

export function AdminPanel(): React.ReactElement {
  const { data, isLoading } = useQuery({
    queryKey: ["model-info"],
    queryFn: fetchModelInfo,
  });

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>
        Operator Dashboard
      </Typography>
      {isLoading && <Typography>Loading model info…</Typography>}
      {data && (
        <Stack spacing={3}>
          <Paper elevation={1} sx={{ p: 3 }}>
            <Typography variant="h6">Active Model</Typography>
            <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
              <Chip label={data.model_version} color="primary" />
              <Chip
                label={data.deploy_env}
                color={data.deploy_env === "prod" ? "error" : "default"}
              />
            </Stack>
          </Paper>
          {data.evaluation && (
            <Paper elevation={1} sx={{ p: 3 }}>
              <Typography variant="h6">Evaluation Metrics</Typography>
              <Box component="pre" sx={{ p: 2, background: "#f5f5f5", borderRadius: 1 }}>
                {JSON.stringify(data.evaluation, null, 2)}
              </Box>
            </Paper>
          )}
          <Paper elevation={1} sx={{ p: 3 }}>
            <Typography variant="h6">Model Card Excerpt</Typography>
            <Box component="pre" sx={{ p: 2, background: "#f5f5f5", borderRadius: 1, whiteSpace: "pre-wrap" }}>
              {data.model_card_excerpt}
            </Box>
          </Paper>
          {data.training && (
            <Paper elevation={1} sx={{ p: 3 }}>
              <Typography variant="h6">Last Training Run</Typography>
              <Box component="pre" sx={{ p: 2, background: "#f5f5f5", borderRadius: 1 }}>
                {JSON.stringify(data.training, null, 2)}
              </Box>
            </Paper>
          )}
          <Alert severity="info">
            All admin actions are recorded to the append-only audit log.
          </Alert>
        </Stack>
      )}
    </Container>
  );
}
