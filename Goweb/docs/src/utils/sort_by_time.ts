/**
 * Sort mảng items theo field thời gian, giảm dần (mới nhất trước).
 * Dùng cho data trả về từ proxy API (merged từ nhiều agents).
 */
export function sortByTime<T extends Record<string, any>>(
  items: T[],
  timeField: string = "create_time"
): T[] {
  if (items.length <= 1) return items;
  return [...items].sort((a, b) => {
    const ta = a[timeField] || "";
    const tb = b[timeField] || "";
    return ta > tb ? -1 : ta < tb ? 1 : 0;
  });
}
