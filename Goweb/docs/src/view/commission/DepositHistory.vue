<template>
  <PageLayout>
    <lay-field>
      <template #title>
        <span class="field-title">
          <lay-icon type="layui-icon-diamond" size="18px"></lay-icon>
          {{ t("deposit_history.title") }}
        </span>
      </template>

      <lay-form :model="searchForm" class="search-form" mode="inline" label-width="auto">
        <lay-form-item :label="t('deposit_history.order_time_label')">
          <lay-date-picker
            v-model="searchForm.dateRange"
            type="date"
            range
            single-panel
            allow-clear
            :placeholder="[t('common.date_start'), t('common.date_end')]"
          ></lay-date-picker>
        </lay-form-item>
        <lay-form-item :label="t('common.username_label')">
          <lay-input v-model="searchForm.username" :placeholder="t('common.username_placeholder')" style="width: 300px"></lay-input>
        </lay-form-item>
        <lay-form-item :label="t('deposit_history.type_label')">
          <lay-select v-model="searchForm.type" :placeholder="t('common.select')" allow-clear searchable style="width: 220px">
            <lay-select-option value="1" :label="t('deposit_history.type_deposit')"></lay-select-option>
            <lay-select-option value="2" :label="t('deposit_history.type_withdraw')"></lay-select-option>
          </lay-select>
        </lay-form-item>
        <lay-form-item :label="t('deposit_history.status_label')">
          <lay-select v-model="searchForm.status" :placeholder="t('common.select')" allow-clear searchable style="width: 180px">
            <lay-select-option value="0" :label="t('deposit_history.status_pending')"></lay-select-option>
            <lay-select-option value="1" :label="t('deposit_history.status_complete')"></lay-select-option>
            <lay-select-option value="2" :label="t('deposit_history.status_processing')"></lay-select-option>
            <lay-select-option value="3" :label="t('deposit_history.status_failed')"></lay-select-option>
          </lay-select>
        </lay-form-item>
        <lay-form-item>
          <lay-button type="primary" @click="handleSearch">
            <lay-icon type="layui-icon-search"></lay-icon> {{ t("common.search") }}
          </lay-button>
          <lay-button @click="handleReset">
            <lay-icon type="layui-icon-refresh"></lay-icon> {{ t("common.reset") }}
          </lay-button>
        </lay-form-item>
      </lay-form>
    </lay-field>

    <lay-table :columns="columns" :data-source="tableData" :default-toolbar="['filter', 'export', 'print']" :loading="loading" :page="pagination" @change="handlePageChange">
    </lay-table>
  </PageLayout>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from "vue";
import { useI18n } from "layui-component/index";
import PageLayout from "../../components/PageLayout.vue";
import api from "../../utils/api";
import feedback from "../../utils/feedback";
import { sortByTime } from "../../utils/sort_by_time";

const { t } = useI18n();
const loading = ref(false);

const searchForm = reactive({
  dateRange: [] as string[],
  username: "",
  type: null as string | null,
  status: null as string | null,
});

const columns = computed(() => [
  { title: t("deposit_history.col_username"), key: "username" },
  { title: t("deposit_history.col_agent"), key: "user_parent_format" },
  { title: t("deposit_history.col_amount"), key: "amount" },
  { title: t("deposit_history.col_type"), key: "type" },
  { title: t("deposit_history.col_status"), key: "status" },
  { title: t("deposit_history.col_order_time"), key: "create_time" },
]);

const tableData = ref([] as any[]);

const pagination = reactive({
  current: 1,
  limit: 10,
  total: 1,
  limits: [10, 20, 30, 40, 50, 60, 70, 80, 90],
  layout: ["prev", "page", "next", "skip", "count", "limit"],
});

async function fetchData() {
  loading.value = true;
  try {
    const params: Record<string, any> = {
      page: pagination.current,
      limit: pagination.limit,
    };
    if (searchForm.dateRange?.[0]) params.start_date = searchForm.dateRange[0];
    if (searchForm.dateRange?.[1]) params.end_date = searchForm.dateRange[1];
    if (searchForm.username) params.username = searchForm.username;
    if (searchForm.type) params.type = searchForm.type;
    if (searchForm.status) params.status = searchForm.status;

    const res = await api.get("/api/proxy/deposit-history", { params });
    tableData.value = sortByTime(res.data.data || [], "create_time");
    pagination.total = res.data.total || 0;
  } catch (err: any) {
    feedback.msgError(err.response?.data?.error || "Tải dữ liệu thất bại");
  } finally {
    loading.value = false;
  }
}

function handleSearch() {
  pagination.current = 1;
  fetchData();
}

function handleReset() {
  searchForm.dateRange = [];
  searchForm.username = "";
  searchForm.type = null;
  searchForm.status = null;
  pagination.current = 1;
  fetchData();
}

function handlePageChange(page: any) {
  pagination.current = page.current;
  pagination.limit = page.limit;
  fetchData();
}

onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.field-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 700;
}
</style>
