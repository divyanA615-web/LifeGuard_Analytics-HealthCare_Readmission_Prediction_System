import React, { useState } from "react";
import {
  Box,
  Container,
  Paper,
  Stack,
  Typography,
  Button,
  TextField,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Alert,
} from "@mui/material";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { phiMask } from "@/security/phiMask";
import { predictPatient, PredictResponse } from "@/hooks/useApi";

const AgeBands = ["[0-10)", "[10-20)", "[20-30)", "[30-40)", "[40-50)", "[50-60)", "[60-70)", "[70-80)", "[80-90)", "[90-100)"];
const PayerCodes = ["BC", "CH", "CM", "CP", "DM", "FR", "HM", "MC", "MD", "MP", "OG", "OT", "PO", "SI", "SP", "WC"];

const PatientSchema = z.object({
  patient_token: z.string().optional(),
  age_band: z.string().min(3),
  age: z.coerce.number().int().min(18).max(110),
  gender_male: z.coerce.number().int().min(0).max(1),
  admission_type_emergency: z.coerce.number().int().min(0).max(1),
  discharge_to_home: z.coerce.number().int().min(0).max(1),
  time_in_hospital: z.coerce.number().int().min(1).max(20),
  num_lab_procedures: z.coerce.number().int().min(0).max(100),
  num_procedures: z.coerce.number().int().min(0).max(20),
  num_medications: z.coerce.number().int().min(0).max(80),
  number_outpatient: z.coerce.number().int().min(0).max(50),
  number_emergency: z.coerce.number().int().min(0).max(50),
  number_inpatient: z.coerce.number().int().min(0).max(50),
  number_diagnoses: z.coerce.number().int().min(1).max(20),
  a1c_result_num: z.coerce.number().int().min(0).max(3),
  max_glu_serum_num: z.coerce.number().int().min(0).max(3),
  insulin_use: z.coerce.number().int().min(0).max(1),
  metformin_use: z.coerce.number().int().min(0).max(1),
  diabetesMed_yes: z.coerce.number().int().min(0).max(1),
  change_in_meds: z.coerce.number().int().min(0).max(1),
  payer_code: z.string().min(2).max(3),
});

type PatientFormData = z.infer<typeof PatientSchema>;

const initialValues: PatientFormData = {
  age_band: "[50-60)",
  age: 55,
  gender_male: 1,
  admission_type_emergency: 1,
  discharge_to_home: 1,
  time_in_hospital: 5,
  num_lab_procedures: 45,
  num_procedures: 1,
  num_medications: 14,
  number_outpatient: 0,
  number_emergency: 0,
  number_inpatient: 0,
  number_diagnoses: 3,
  a1c_result_num: 0,
  max_glu_serum_num: 0,
  insulin_use: 1,
  metformin_use: 1,
  diabetesMed_yes: 1,
  change_in_meds: 0,
  payer_code: "MC",
};

export function PatientForm(): React.ReactElement {
  const [values, setValues] = useState<PatientFormData>(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [serverError, setServerError] = useState<string>();
  const navigate = useNavigate();

  const handleChange =
    (key: keyof PatientFormData) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
      const val = e.target.value;
      setValues((prev) => ({ ...prev, [key]: val }));
    };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError(undefined);
    const parsed = PatientSchema.safeParse(values);
    if (!parsed.success) {
      const fieldErrors: Record<string, string> = {};
      parsed.error.issues.forEach((issue) => {
        const path = issue.path.join(".");
        fieldErrors[path] = issue.message;
      });
      setErrors(fieldErrors);
      return;
    }
    setErrors({});
    setBusy(true);
    try {
      const result: PredictResponse = await predictPatient(values);
      navigate(`/patients/${result.patient_token}/predict`, { state: result });
    } catch (err: any) {
      setServerError(err?.response?.data?.detail ?? "Prediction failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 8 }}>
      <Paper elevation={2} sx={{ p: 4 }}>
        <Typography variant="h5" component="h1" sx={{ mb: 2 }}>
          Patient Intake Form
        </Typography>
        <Typography variant="body2" sx={{ mb: 3 }} color="text.secondary">
          All identifiers stay in your browser. Submission is end-to-end
          encrypted with keys backed by Cloud KMS.
          {phiMask("PHI fields are masked automatically on display.")}
        </Typography>

        {serverError && <Alert severity="error">{serverError}</Alert>}

        <Box component="form" onSubmit={onSubmit}>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ mb: 2 }}>
            <TextField
              select
              label="Age band"
              value={values.age_band}
              onChange={handleChange("age_band")}
              fullWidth
              required
              error={!!errors.age_band}
              helperText={errors.age_band ?? ""}
            >
              {AgeBands.map((band) => (
                <MenuItem key={band} value={band}>
                  {band}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Age"
              type="number"
              value={values.age}
              onChange={handleChange("age")}
              fullWidth
              error={!!errors.age}
              helperText={errors.age ?? ""}
            />
            <TextField
              select
              label="Payer code"
              value={values.payer_code}
              onChange={handleChange("payer_code")}
              fullWidth
              error={!!errors.payer_code}
              helperText={errors.payer_code ?? ""}
            >
              {PayerCodes.map((p) => (
                <MenuItem key={p} value={p}>
                  {p}
                </MenuItem>
              ))}
            </TextField>
          </Stack>

          <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ mb: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={values.gender_male === 1}
                  onChange={(e) =>
                    setValues((prev) => ({
                      ...prev,
                      gender_male: e.target.checked ? 1 : 0,
                    }))
                  }
                />
              }
              label="Male"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={values.admission_type_emergency === 1}
                  onChange={(e) =>
                    setValues((prev) => ({
                      ...prev,
                      admission_type_emergency: e.target.checked ? 1 : 0,
                    }))
                  }
                />
              }
              label="Emergency admission"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={values.discharge_to_home === 1}
                  onChange={(e) =>
                    setValues((prev) => ({
                      ...prev,
                      discharge_to_home: e.target.checked ? 1 : 0,
                    }))
                  }
                />
              }
              label="Discharge to home"
            />
          </Stack>

          <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ mb: 2 }}>
            <TextField
              label="Time in hospital (days)"
              type="number"
              value={values.time_in_hospital}
              onChange={handleChange("time_in_hospital")}
              fullWidth
              error={!!errors.time_in_hospital}
              helperText={errors.time_in_hospital ?? ""}
            />
            <TextField
              label="Lab procedures"
              type="number"
              value={values.num_lab_procedures}
              onChange={handleChange("num_lab_procedures")}
              fullWidth
            />
            <TextField
              label="Total procedures"
              type="number"
              value={values.num_procedures}
              onChange={handleChange("num_procedures")}
              fullWidth
            />
            <TextField
              label="Medications"
              type="number"
              value={values.num_medications}
              onChange={handleChange("num_medications")}
              fullWidth
            />
          </Stack>

          <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ mb: 2 }}>
            <TextField
              label="Outpatient visits"
              type="number"
              value={values.number_outpatient}
              onChange={handleChange("number_outpatient")}
              fullWidth
            />
            <TextField
              label="Emergency visits"
              type="number"
              value={values.number_emergency}
              onChange={handleChange("number_emergency")}
              fullWidth
            />
            <TextField
              label="Inpatient visits"
              type="number"
              value={values.number_inpatient}
              onChange={handleChange("number_inpatient")}
              fullWidth
            />
            <TextField
              label="Diagnosis count"
              type="number"
              value={values.number_diagnoses}
              onChange={handleChange("number_diagnoses")}
              fullWidth
            />
          </Stack>

          <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ mb: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={values.diabetesMed_yes === 1}
                  onChange={(e) =>
                    setValues((prev) => ({
                      ...prev,
                      diabetesMed_yes: e.target.checked ? 1 : 0,
                    }))
                  }
                />
              }
              label="Diabetes prescription"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={values.insulin_use === 1}
                  onChange={(e) =>
                    setValues((prev) => ({
                      ...prev,
                      insulin_use: e.target.checked ? 1 : 0,
                    }))
                  }
                />
              }
              label="Insulin"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={values.metformin_use === 1}
                  onChange={(e) =>
                    setValues((prev) => ({
                      ...prev,
                      metformin_use: e.target.checked ? 1 : 0,
                    }))
                  }
                />
              }
              label="Metformin"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={values.change_in_meds === 1}
                  onChange={(e) =>
                    setValues((prev) => ({
                      ...prev,
                      change_in_meds: e.target.checked ? 1 : 0,
                    }))
                  }
                />
              }
              label="Recent medication change"
            />
          </Stack>

          <Stack direction="row" spacing={2} sx={{ justifyContent: "flex-end" }}>
            <Button
              variant="outlined"
              onClick={() => navigate(-1)}
              disabled={busy}
            >
              Cancel
            </Button>
            <Button type="submit" variant="contained" disabled={busy}>
              {busy ? "Predicting…" : "Predict Readmission Risk"}
            </Button>
          </Stack>
        </Box>
      </Paper>
    </Container>
  );
}
