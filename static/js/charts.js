Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
Chart.defaults.color = '#6c757d';
const palette = ['#0d6efd','#198754','#ffc107','#dc3545','#6f42c1','#20c997','#fd7e14'];
function baseChart(canvasId, config){ const ctx = document.getElementById(canvasId); if(!ctx) return null; return new Chart(ctx, config); }
function initRevenueChart(canvasId, labels, data){ return baseChart(canvasId, {type:'line', data:{labels, datasets:[{label:'Revenue', data, borderColor:palette[0], backgroundColor:'rgba(13,110,253,.15)', fill:true, tension:.35}]}, options:{responsive:true}}); }
function initPatientChart(canvasId, labels, data){ return baseChart(canvasId, {type:'bar', data:{labels, datasets:[{label:'Patients', data, backgroundColor:palette[2], borderRadius:8}]}, options:{responsive:true}}); }
function initDepartmentChart(canvasId, labels, data){ return baseChart(canvasId, {type:'pie', data:{labels, datasets:[{data, backgroundColor:palette}]}, options:{responsive:true}}); }
function initBedOccupancyChart(canvasId, data){ return baseChart(canvasId, {type:'doughnut', data:{labels:['Occupied','Available'], datasets:[{data, backgroundColor:[palette[3], palette[1]]}]}}); }
function initAIForecastChart(canvasId, historical, forecast){ return baseChart(canvasId, {type:'line', data:{labels:[...historical.map(x=>x.date), ...forecast.map(x=>x.date)], datasets:[{label:'Historical', data:historical.map(x=>x.value), borderColor:palette[0], tension:.3},{label:'Forecast', data:[...Array(historical.length).fill(null), ...forecast.map(x=>x.value)], borderColor:palette[4], borderDash:[6,4], tension:.3}]}}); }
window.ChartUtils = {initRevenueChart, initPatientChart, initDepartmentChart, initBedOccupancyChart, initAIForecastChart};
