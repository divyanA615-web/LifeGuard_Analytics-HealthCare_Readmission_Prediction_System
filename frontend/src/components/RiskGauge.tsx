import React from "react";
import { Box, Typography } from "@mui/material";

interface RiskGaugeProps {
  value: number;
  label: "LOW" | "MEDIUM" | "HIGH";
}

export function RiskGauge({ value, label }: RiskGaugeProps): React.ReactElement {
  const clamped = Math.max(0, Math.min(value, 1));
  const degrees = clamped * 180;
  const color =
    label === "HIGH" ? "#d32f2f" : label === "MEDIUM" ? "#f57c00" : "#388e3c";

  return (
    <Box sx={{ width: 260, height: 160, position: "relative" }}>
      <svg viewBox="0 0 200 110" width="100%" height="100%">
        <defs>
          <linearGradient id="risk-fill" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#388e3c" />
            <stop offset="50%" stopColor="#f57c00" />
            <stop offset="100%" stopColor="#d32f2f" />
          </linearGradient>
        </defs>
        <path
          d="M 10 100 A 90 90 0 0 1 190 100"
          fill="none"
          stroke="url(#risk-fill)"
          strokeWidth="18"
        />
        <line
          x1="100"
          y1="100"
          x2={100 - 80 * Math.cos(Math.PI * (1 - degrees / 180))}
          y2={100 - 80 * Math.sin(Math.PI * (1 - degrees / 180))}
          stroke={color}
          strokeWidth="4"
        />
        <circle cx="100" cy="100" r="6" fill={color} />
      </svg>
      <Box
        sx={{
          position: "absolute",
          top: "60%",
          left: 0,
          width: "100%",
          textAlign: "center",
        }}
      >
        <Typography variant="h3" sx={{ color, fontWeight: 800 }}>
          {(clamped * 100).toFixed(0)}%
        </Typography>
        <Typography variant="button" sx={{ color }}>
          {label} RISK
        </Typography>
      </Box>
    </Box>
  );
}
