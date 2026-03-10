<template>
  <PageLayout>
    <lay-field>
      <template #title>
        <span class="field-title">
          <lay-icon type="layui-icon-form" size="18px"></lay-icon>
          {{ t("provider_bets.title") }}
        </span>
      </template>

      <lay-form :model="searchForm" class="search-form" mode="inline" label-width="auto">
        <lay-form-item :label="t('provider_bets.bet_time_label')">
          <lay-date-picker
            v-model="dateForm.dateRange"
            type="date"
            range
            single-panel
            allow-clear
            :placeholder="[t('common.date_start'), t('common.date_end')]"
          ></lay-date-picker>
        </lay-form-item>
        <lay-form-item>
          <lay-select v-model="dateForm.quickDate" :placeholder="t('common.today')" fit-content @change="onQuickDateChange">
            <lay-select-option :value="quickDateValues.today" :label="t('common.today')"></lay-select-option>
            <lay-select-option :value="quickDateValues.yesterday" :label="t('common.yesterday')"></lay-select-option>
            <lay-select-option :value="quickDateValues.thisWeek" :label="t('common.this_week')"></lay-select-option>
            <lay-select-option :value="quickDateValues.thisMonth" :label="t('common.this_month')"></lay-select-option>
            <lay-select-option :value="quickDateValues.lastMonth" :label="t('common.last_month')"></lay-select-option>
          </lay-select>
        </lay-form-item>
        <lay-form-item :label="t('provider_bets.serial_label')">
          <lay-input v-model="searchForm.serialNo" :placeholder="t('provider_bets.serial_placeholder')" style="width: 200px"></lay-input>
        </lay-form-item>
        <lay-form-item :label="t('provider_bets.platform_user_label')">
          <lay-input v-model="searchForm.platformUsername" :placeholder="t('provider_bets.platform_user_placeholder')" style="width: 200px"></lay-input>
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

    <lay-table :columns="columns" :data-source="tableData" :default-toolbar="['filter', 'export', 'print']" :page="pagination" @change="handlePageChange">
    </lay-table>
  </PageLayout>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from "vue";
import { useI18n } from "layui-component/index";
import PageLayout from "../../components/PageLayout.vue";
import { useQuickDate } from "../../composables/useQuickDate";

const { t } = useI18n();
const { quickDateValues, dateForm, onQuickDateChange, resetDate } = useQuickDate();

const searchForm = reactive({
  serialNo: "",
  platformUsername: "",
});

const columns = computed(() => [
  { title: t("provider_bets.col_serial"), key: "serial_no", width: "250px" },
  { title: t("provider_bets.col_provider"), key: "platform_id_name", minWidth: "150px" },
  { title: t("provider_bets.col_platform_user"), key: "platform_username", minWidth: "150px" },
  { title: t("provider_bets.col_game_type"), key: "c_name", minWidth: "150px" },
  { title: t("provider_bets.col_game_name"), key: "game_name", minWidth: "150px" },
  { title: t("provider_bets.col_bet_amount"), key: "bet_amount", minWidth: "150px" },
  { title: t("provider_bets.col_valid_bet"), key: "turnover", minWidth: "150px" },
  { title: t("provider_bets.col_bonus"), key: "prize", minWidth: "150px" },
  { title: t("provider_bets.col_win_loss"), key: "win_lose", minWidth: "150px" },
  { title: t("provider_bets.col_bet_time"), key: "bet_time", minWidth: "160px" },
]);

const tableData = ref([] as any[]);

const pagination = reactive({
  current: 1,
  limit: 10,
  total: 1,
  limits: [10, 20, 30, 40, 50, 60, 70, 80, 90],
  layout: ["prev", "page", "next", "skip", "count", "limit"],
});

function handleSearch() {
  console.log("search", { ...dateForm, ...searchForm });
}

function handleReset() {
  resetDate();
  searchForm.serialNo = "";
  searchForm.platformUsername = "";
}

function handlePageChange(page: any) {
  pagination.current = page.current;
  pagination.limit = page.limit;
}
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
