import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface KPICardProps {
  label: string;
  value: string | number;
  sub?: string;
}

export default function KPICard({ label, value, sub }: KPICardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-gray-500 font-medium">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold text-gray-900">{value}</p>
        {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
      </CardContent>
    </Card>
  );
}
