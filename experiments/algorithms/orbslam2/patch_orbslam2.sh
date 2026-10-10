#!/usr/bin/env bash
# Patches mínimos no ORB-SLAM2 (commit f2e6f51) para o PIBIC. Falha se algum patch obrigatório não casar.
# Uso: patch_orbslam2.sh <dir_ORB_SLAM2> <queenscamp_runner.cc>
set -euo pipefail
D="$1"
RUNNER="$2"

# 1) GCC 7: usleep/getenv sem include explícito.
for f in "$D"/src/*.cc "$D"/Examples/*/*.cc; do
  sed -i '1i #include <cstdlib>' "$f"
  sed -i '1i #include <unistd.h>' "$f"
done

# 2) VO pura: com ORBSLAM2_NO_LOOP definido, nenhum keyframe entra na fila do LoopClosing.
#    A thread continua viva (o Shutdown() espera por ela), mas nunca detecta loops.
sed -i 's/if(pKF->mnId!=0)/if(pKF->mnId!=0 \&\& std::getenv("ORBSLAM2_NO_LOOP")==NULL)/' "$D/src/LoopClosing.cc"
grep -q 'ORBSLAM2_NO_LOOP' "$D/src/LoopClosing.cc" || { echo "patch do loop closing falhou"; exit 1; }

# 3) Permitir SaveTrajectoryTUM no modo monocular (trajetória de todos os quadros, não só keyframes).
perl -0pi -e 's/if\(mSensor==MONOCULAR\)\s*\{\s*cerr << "ERROR: SaveTrajectoryTUM cannot be used for monocular\." << endl;\s*return;\s*\}//' "$D/src/System.cc"
if grep -q 'SaveTrajectoryTUM cannot be used for monocular' "$D/src/System.cc"; then
  echo "patch do SaveTrajectoryTUM monocular falhou"; exit 1
fi

# 4) Eigen 3.3+: value_type do alocador precisa ser pair<Key const, T>.
sed -i 's/std::pair<const KeyFrame\*, g2o::Sim3>/std::pair<KeyFrame* const, g2o::Sim3>/' "$D/include/LoopClosing.h"

# 5) make -j sem limite estoura a memória; usar o número de núcleos.
sed -i 's/make -j$/make -j"$(nproc)"/' "$D/build.sh"

# 6) Runner do PIBIC (mono/RGB-D a partir de listas, estado de rastreamento por quadro).
cp "$RUNNER" "$D/Examples/RGB-D/queenscamp_runner.cc"
cat >> "$D/CMakeLists.txt" <<'EOF'

add_executable(queenscamp_runner Examples/RGB-D/queenscamp_runner.cc)
target_link_libraries(queenscamp_runner ${PROJECT_NAME})
set_target_properties(queenscamp_runner PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR})
EOF
echo "patches aplicados"
