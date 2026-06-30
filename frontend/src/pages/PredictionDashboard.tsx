import React from "react";
import {
  Container,
  Paper,
  Typography,
  Box,
  Stack,
  Toolbar,
  Button,
} from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import { RiskGauge } from "@/components/RiskGauge";
import { SHAPWaterfall } from "@/components/SHAPWaterfall";
import { ExplanationCard } from "@/components/ExplanationCard";
import { SimilarPatients } from "@/components/SimilarPatients";
import { PredictResponse } from "@/hooks/useApi";

interface DashboardLocationState {
  result: PredictResponse;
}

export function PredictionDashboard(): React.ReactElement {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as DashboardLocationState | undefined;
  const result = state?.result;

  if (!result) {
    return (
      <Container sx={{ mt: 4 }}>
        <Typography color="error">
          Prediction state missing. Please go back to the intake form.
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
      <Typography variant="h4" component="h1" sx={{ mb: 3 }}>
        Prediction Result
      </Typography>

      <Stack direction={{ xs: "column", md: "row" }} spacing={3}>
        <Box sx={{ flex: 1 }}>
          <Paper elevation={2} sx={{ p: 4 }}>
            <Typography variant="h6">Patient Readmission Risk</Typography>
            <Box sx={{ display: "flex", justifyContent: "center", my: 3 }}>
              <RiskGauge value={result.risk_proba} label={result.risk_label} />
            </Box>
            <Typography variant="body2" color="text.secondary" align="center">
              Model: <code>{result.model_version}</code> ·
              Latency: {result.latency_ms.toFixed(1)}ms
            </Typography>
          </Paper>
        </Box>
        <Box sx={{ flex: 1 }}>
          <Paper elevation={2} sx={{ p: 4 }}>
            <Typography variant="h6">SHAP Attribution</Typography>
            <SHAPWaterfall data={result.explanation} />
          </Paper>
        </Box>
      </Stack>

      <Paper elevation={2} sx={{ p: 4, mt: 3 }}>
        <Typography variant="h6">Clinical Explanation</Typography>
        <ExplanationCard text={result.humane_explanation ?? "AI explanation pending."} />
      </Paper>

      <Paper elevation={2} sx={{ p: 4, mt: 3 }}>
        <Typography variant="h6">Similar Patients (k-anonymized)</Typography>
        <SimilarPatients
          rows={result.similar_patients ?? []}
        />
      </Paper>

      <Toolbar sx={{ justifyContent: "flex-end" }}>
        <Button onClick={() => navigate(`/patients/${result.patient_token}`)}>
          View Patient Timeline
        </Button>
        <Button variant="contained" color="primary" sx={{ ml: 2 }}>
          Acknowledge & Plan Follow-up
        </Button>
      </Toolbar>
    </Container>
  );
}
