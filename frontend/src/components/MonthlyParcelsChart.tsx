import { Box, Typography, useTheme } from "@mui/material";
import { useState } from "react";

import type { MonthlyCount } from "../types";

// Logical coordinate space for the SVG viewBox. Kept in the same rough
// units as real pixels (no `preserveAspectRatio="none"`, no independent
// width/height override) so text and marks scale uniformly instead of
// stretching - the SVG's intrinsic aspect ratio drives its rendered
// height as the responsive width changes.
const CHART_WIDTH = 600;
const CHART_HEIGHT = 180;
const AXIS_HEIGHT = 26;
const MAX_BAR_WIDTH = 28;

function niceMax(value: number): number {
  if (value <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const normalized = value / magnitude;
  const step = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return step * magnitude;
}

function formatMonth(month: string): string {
  const [year, monthNumber] = month.split("-").map(Number);
  return new Date(year, monthNumber - 1, 1).toLocaleDateString(undefined, { month: "short" });
}

interface MonthlyParcelsChartProps {
  data: MonthlyCount[];
}

export function MonthlyParcelsChart({ data }: MonthlyParcelsChartProps) {
  const theme = useTheme();
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const maxCount = niceMax(Math.max(...data.map((entry) => entry.count), 1));
  const gridlineValues = [0, maxCount / 2, maxCount];

  const slotWidth = CHART_WIDTH / data.length;
  const barWidth = Math.min(MAX_BAR_WIDTH, slotWidth * 0.5);

  return (
    <Box sx={{ position: "relative" }}>
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT + AXIS_HEIGHT}`}
        width="100%"
        role="img"
        aria-label={`Parcels per month: ${data
          .map((d) => `${formatMonth(d.month)} ${d.count}`)
          .join(", ")}`}
      >
        {gridlineValues.map((value) => {
          const y = CHART_HEIGHT - (value / maxCount) * CHART_HEIGHT;
          return (
            <line
              key={value}
              x1={0}
              x2={CHART_WIDTH}
              y1={y}
              y2={y}
              stroke={theme.palette.divider}
              strokeWidth={1}
            />
          );
        })}

        {data.map((entry, index) => {
          const barHeight = (entry.count / maxCount) * CHART_HEIGHT;
          const centerX = slotWidth * index + slotWidth / 2;
          const x = centerX - barWidth / 2;
          const isHovered = hoveredIndex === index;

          return (
            <g key={entry.month}>
              <rect
                x={x}
                y={CHART_HEIGHT - barHeight}
                width={barWidth}
                height={Math.max(barHeight, entry.count > 0 ? 2 : 0)}
                rx={3}
                fill={theme.palette.primary.main}
                opacity={isHovered ? 1 : 0.85}
                onMouseEnter={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(null)}
                style={{ cursor: "pointer", transition: "opacity 0.1s" }}
              >
                <title>
                  {formatMonth(entry.month)} {entry.month.slice(0, 4)}: {entry.count} parcel
                  {entry.count === 1 ? "" : "s"}
                </title>
              </rect>
              <text
                x={centerX}
                y={CHART_HEIGHT + AXIS_HEIGHT / 2 + 5}
                fontSize={12}
                textAnchor="middle"
                fill={theme.palette.text.secondary}
              >
                {formatMonth(entry.month)}
              </text>
            </g>
          );
        })}
      </svg>

      {hoveredIndex !== null && (
        <Box
          sx={{
            position: "absolute",
            top: 0,
            left: `${((hoveredIndex + 0.5) / data.length) * 100}%`,
            transform: "translate(-50%, -100%)",
            bgcolor: "background.paper",
            border: 1,
            borderColor: "divider",
            borderRadius: 1,
            px: 1,
            py: 0.5,
            boxShadow: 2,
            pointerEvents: "none",
            whiteSpace: "nowrap",
          }}
        >
          <Typography variant="caption" sx={{ fontWeight: 600 }}>
            {data[hoveredIndex].count} parcel{data[hoveredIndex].count === 1 ? "" : "s"}
          </Typography>
        </Box>
      )}
    </Box>
  );
}
