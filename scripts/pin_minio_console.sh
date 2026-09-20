#!/usr/bin/env bash
#
# 把 MinIO Web 控制台（WebUI）固定到 127.0.0.1:9001。
#
# 背景：MinIO 在未指定 --console-address 时会为 WebUI 随机分配端口，
# 每次重启地址都会变（本机实测出现过 64082 / 56187 / 64989 / 54595）。
# 本脚本把 --console-address 写入 brew 的 service 定义（plist），
# 之后用 `brew services run minio` 启动，控制台就固定监听 9001。
#
# 重复执行安全（幂等）；brew upgrade / reinstall minio 会按 formula
# 重新生成 plist，升级后重新执行一次本脚本即可。
#
# 用法：
#   ./scripts/pin_minio_console.sh
#   MINIO_CONSOLE_ADDR=:9001 ./scripts/pin_minio_console.sh   # 需要局域网访问时
#
# 生效方式：
#   brew services stop minio && brew services run minio
#
set -euo pipefail

CONSOLE_ADDR="${MINIO_CONSOLE_ADDR:-127.0.0.1:9001}"
PLIST="$(brew --prefix)/opt/minio/sh.brew.minio.plist"
PLIST_BUDDY="/usr/libexec/PlistBuddy"

if [ ! -f "${PLIST}" ]; then
  echo "找不到 ${PLIST}，请先执行 brew install minio" >&2
  exit 1
fi

# 1. 读出当前 ProgramArguments（去掉 PlistBuddy 打印的 Array { / } 两行）
args=()
while IFS= read -r line; do
  args+=("${line}")
done < <("${PLIST_BUDDY}" -c "Print :ProgramArguments" "${PLIST}" \
          | sed -e '1d' -e '$d' -e 's/^[[:space:]]*//')

if [ "${#args[@]}" -lt 2 ]; then
  echo "解析 ProgramArguments 失败，请检查 ${PLIST}" >&2
  exit 1
fi

# 2. 去掉已存在的 --console-address，避免重复写入
filtered=()
for arg in "${args[@]}"; do
  case "${arg}" in
    --console-address=*) continue ;;
  esac
  filtered+=("${arg}")
done

# 3. 把 --console-address 插到最后一个参数（数据目录）之前
last_index=$(( ${#filtered[@]} - 1 ))
target=(
  "${filtered[@]:0:${last_index}}"
  "--console-address=${CONSOLE_ADDR}"
  "${filtered[${last_index}]}"
)

# 4. 整体重写 ProgramArguments
"${PLIST_BUDDY}" -c "Delete :ProgramArguments" "${PLIST}" >/dev/null
"${PLIST_BUDDY}" -c "Add :ProgramArguments array" "${PLIST}" >/dev/null
index=0
for arg in "${target[@]}"; do
  "${PLIST_BUDDY}" -c "Add :ProgramArguments:${index} string ${arg}" "${PLIST}" >/dev/null
  index=$((index + 1))
done

echo "已写入 ${PLIST}"
"${PLIST_BUDDY}" -c "Print :ProgramArguments" "${PLIST}"
echo
echo "控制台地址固定为：http://${CONSOLE_ADDR}"
echo "生效方式：brew services stop minio && brew services run minio"
