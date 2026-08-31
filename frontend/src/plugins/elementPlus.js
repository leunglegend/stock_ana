import { ElBadge } from 'element-plus/es/components/badge/index.mjs'
import { ElButton } from 'element-plus/es/components/button/index.mjs'
import { ElCard } from 'element-plus/es/components/card/index.mjs'
import { ElCheckbox } from 'element-plus/es/components/checkbox/index.mjs'
import { ElCol } from 'element-plus/es/components/col/index.mjs'
import { ElDialog } from 'element-plus/es/components/dialog/index.mjs'
import { ElDivider } from 'element-plus/es/components/divider/index.mjs'
import { ElDrawer } from 'element-plus/es/components/drawer/index.mjs'
import { ElDropdown, ElDropdownItem, ElDropdownMenu } from 'element-plus/es/components/dropdown/index.mjs'
import { ElEmpty } from 'element-plus/es/components/empty/index.mjs'
import { ElForm, ElFormItem } from 'element-plus/es/components/form/index.mjs'
import { ElIcon } from 'element-plus/es/components/icon/index.mjs'
import { ElInput } from 'element-plus/es/components/input/index.mjs'
import { ElInputNumber } from 'element-plus/es/components/input-number/index.mjs'
import { ElLoading } from 'element-plus/es/components/loading/index.mjs'
import { ElPagination } from 'element-plus/es/components/pagination/index.mjs'
import { ElProgress } from 'element-plus/es/components/progress/index.mjs'
import { ElRadioButton, ElRadioGroup } from 'element-plus/es/components/radio/index.mjs'
import { ElRow } from 'element-plus/es/components/row/index.mjs'
import { ElSegmented } from 'element-plus/es/components/segmented/index.mjs'
import { ElOption, ElSelect } from 'element-plus/es/components/select/index.mjs'
import { ElSwitch } from 'element-plus/es/components/switch/index.mjs'
import { ElTabPane, ElTabs } from 'element-plus/es/components/tabs/index.mjs'
import { ElTable, ElTableColumn } from 'element-plus/es/components/table/index.mjs'
import { ElTooltip } from 'element-plus/es/components/tooltip/index.mjs'
import {
  DataAnalysis,
  Document,
  DocumentRemove,
  Loading,
  Monitor,
  Money,
  Odometer,
  Reading,
  Search,
  Star,
  TrendCharts,
  WarningFilled,
} from '@element-plus/icons-vue'

import 'element-plus/es/components/base/style/css'
import 'element-plus/es/components/badge/style/css'
import 'element-plus/es/components/button/style/css'
import 'element-plus/es/components/card/style/css'
import 'element-plus/es/components/checkbox/style/css'
import 'element-plus/es/components/col/style/css'
import 'element-plus/es/components/dialog/style/css'
import 'element-plus/es/components/divider/style/css'
import 'element-plus/es/components/drawer/style/css'
import 'element-plus/es/components/dropdown/style/css'
import 'element-plus/es/components/empty/style/css'
import 'element-plus/es/components/form/style/css'
import 'element-plus/es/components/icon/style/css'
import 'element-plus/es/components/input/style/css'
import 'element-plus/es/components/input-number/style/css'
import 'element-plus/es/components/loading/style/css'
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/es/components/option/style/css'
import 'element-plus/es/components/pagination/style/css'
import 'element-plus/es/components/progress/style/css'
import 'element-plus/es/components/radio-button/style/css'
import 'element-plus/es/components/radio-group/style/css'
import 'element-plus/es/components/row/style/css'
import 'element-plus/es/components/segmented/style/css'
import 'element-plus/es/components/select/style/css'
import 'element-plus/es/components/switch/style/css'
import 'element-plus/es/components/table/style/css'
import 'element-plus/es/components/tabs/style/css'
import 'element-plus/es/components/tooltip/style/css'

const components = [
  ElBadge, ElButton, ElCard, ElCheckbox, ElCol, ElDialog, ElDivider, ElDrawer,
  ElDropdown, ElDropdownItem, ElDropdownMenu, ElEmpty, ElForm, ElFormItem,
  ElIcon, ElInput, ElInputNumber, ElOption, ElPagination, ElProgress, ElRadioButton,
  ElRadioGroup, ElRow, ElSegmented, ElSelect, ElSwitch, ElTabPane, ElTable, ElTableColumn, ElTabs,
  ElTooltip,
]

const icons = {
  DataAnalysis,
  Document,
  DocumentRemove,
  Loading,
  Monitor,
  Money,
  Odometer,
  Reading,
  Search,
  Star,
  TrendCharts,
  WarningFilled,
}

export function installElementPlus(app) {
  components.forEach((component) => app.component(component.name, component))
  Object.entries(icons).forEach(([name, component]) => app.component(name, component))
  app.use(ElLoading)
}
