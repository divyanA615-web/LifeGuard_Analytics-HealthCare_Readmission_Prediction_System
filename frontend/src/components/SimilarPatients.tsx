import React from "react";
import {
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Typography,
} from "@mui/material";

interface SimilarPatientsProps {
  rows: { patient_token: string; similarity: number }[];
}

export function SimilarPatients({ rows }: SimilarPatientsProps): React.ReactElement {
  if (!rows || rows.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No similar patients found in the de-identified cohort.
      </Typography>
    );
  }
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Patient Token</TableCell>
          <TableCell align="right">Cosine similarity</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.patient_token}>
            <TableCell>{row.patient_token}</TableCell>
            <TableCell align="right">{row.similarity.toFixed(3)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
