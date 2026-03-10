import { reactive } from "vue";

function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function useQuickDate(options?: { onlyTodayYesterday?: boolean }) {
  const now = new Date();
  const today = formatDate(now);

  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);

  const quickDateValues: Record<string, string> = {
    today: `${today} | ${today}`,
    yesterday: `${formatDate(yesterday)} | ${formatDate(yesterday)}`,
  };

  if (!options?.onlyTodayYesterday) {
    const weekStart = new Date(now);
    weekStart.setDate(weekStart.getDate() - weekStart.getDay() + 1);

    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastMonthStart = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0);

    quickDateValues.thisWeek = `${formatDate(weekStart)} | ${today}`;
    quickDateValues.thisMonth = `${formatDate(monthStart)} | ${today}`;
    quickDateValues.lastMonth = `${formatDate(lastMonthStart)} | ${formatDate(lastMonthEnd)}`;
  }

  const dateForm = reactive({
    dateRange: [today, today] as string[],
    quickDate: quickDateValues.today,
  });

  function onQuickDateChange(val: string) {
    if (val) {
      const parts = val.split(" | ");
      dateForm.dateRange = [parts[0], parts[1]];
    }
  }

  function resetDate() {
    dateForm.dateRange = [today, today];
    dateForm.quickDate = quickDateValues.today;
  }

  return { today, quickDateValues, dateForm, onQuickDateChange, resetDate };
}
