// 18420.5 -> "18,420.50". Callers add the $ sign themselves.
const formatMoney = (value) => {
  return Number(value || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default formatMoney
