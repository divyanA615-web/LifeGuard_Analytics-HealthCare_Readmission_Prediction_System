import React from "react";
import {
  Container,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useParams, Link as RouterLink } from "react-router-dom";
import { fetchHistory } from "@/hooks/useApi";

export function PatientTimeline(): React.ReactElement {
  const { token = "" } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["history", token],
    queryFn: () => fetchHistory(token, 50),
  });

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>
        Patient Timeline
      </Typography>
      {isLoading && <Typography>Loading…</Typography>}
      {error && (
        <Typography color="error">Failed to load prediction history.</Typography>
      )}
      {data && (
        <Paper elevation={2} sx={{ p: 2 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Predicted at</TableCell>
                <TableCell>Risk</TableCell>
                <TableCell>Model</TableCell>
                <TableCell>Reviewed</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.predictions.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    No predictions yet.
                  </TableCell>
                </TableRow>
              )}
              {data.predictions.map((p: Record<string, unknown>) => (
                <TableRow key={String(p.id)}>
                  <TableCell>{String(p.created_at)}</TableCell>
                  <TableCell>{String(p.risk_label)}</TableCell>
                  <TableCell>{String(p.model_version)}</TableCell>
                  <TableCell>
                    {(p.feedback_recorded as boolean) ? (
                      "✓"
                    ) : (
                      <RouterLink to={`/patients/${token}/predict`}>
                        Review
                      </RouterLink>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}
    </Container>
  );
}
