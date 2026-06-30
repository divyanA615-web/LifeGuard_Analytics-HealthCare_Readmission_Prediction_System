import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface SHAPWaterfallProps {
  data: { feature: string; value: number; contribution: number }[];
}

export function SHAPWaterfall({ data }: SHAPWaterfallProps): React.ReactElement {
  const sorted = [...data]
    .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))
    .slice(0, 10);

  return (
    <div style={{ width: "100%", height: 320 }}>
      <ResponsiveContainer>
        <BarChart data={sorted} layout="vertical" margin={{ left: 8 }}>
          <XAxis type="number" hide />
          <YAxis
            dataKey="feature"
            type="category"
            width={120}
            interval={0}
          />
          <Tooltip />
          <Bar dataKey="contribution">
            {sorted.map((entry, idx) => (
              <Cell
                key={idx}
                fill={entry.contribution >= 0 ? "#d32f2f" : "#1976d2"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
