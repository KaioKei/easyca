
function list_stores(){
  if [ -f "${BUILD_STORES_FILE}" ];then
      stores=$(cat "${BUILD_STORES_FILE}")
      for store_dir in ${stores[*]}; do
          cat "${store_dir}/.name"
          store_list=$(ls "${store_dir}")
          for store in ${store_list[*]}; do
            printf "└──%s\n" "$(basename "${store}")"
          done
      done
  fi
}

function purge_stores() {
    if [ -f "${BUILD_STORES_FILE}" ]; then
        stores=$(cat "${BUILD_STORES_FILE}")
        for store in ${stores[*]}; do
            rm -rf "${store}"
            printf ". Removed %s\n" "${store}"
        done
        rm "${BUILD_STORES_FILE}"
    fi
}