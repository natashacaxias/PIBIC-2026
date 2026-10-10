// Executa o ORB-SLAM2 numa lista de quadros e grava a trajetória TUM e o estado de rastreamento.
//
// Uso: queenscamp_runner VOCABULARIO CONFIG mono|rgbd LISTA DIR_SAIDA [--realtime]
//   LISTA mono: "t caminho_rgb" por linha; rgbd: "t caminho_rgb t caminho_profundidade".
//   --realtime espera o intervalo entre timestamps, como os exemplos oficiais.
// Saídas em DIR_SAIDA: trajectory_tum.txt (todos os quadros rastreados), keyframes_tum.txt,
//   frames.csv (timestamp, estado de rastreamento, ms de tracking).
//   Estados: -1 não pronto, 0 sem imagem, 1 não inicializado, 2 OK, 3 perdido.

#include <chrono>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>

#include <System.h>

using namespace std;

struct Frame {
    double t;
    string rgb;
    string depth;
};

static vector<Frame> LoadList(const string &path, bool rgbd) {
    vector<Frame> frames;
    ifstream f(path.c_str());
    string line;
    while (getline(f, line)) {
        if (line.empty() || line[0] == '#') continue;
        istringstream ss(line);
        Frame frame;
        double tDepth = 0;
        ss >> frame.t >> frame.rgb;
        if (rgbd) ss >> tDepth >> frame.depth;
        frames.push_back(frame);
    }
    return frames;
}

int main(int argc, char **argv) {
    if (argc < 6) {
        cerr << "Uso: " << argv[0] << " VOCABULARIO CONFIG mono|rgbd LISTA DIR_SAIDA [--realtime]" << endl;
        return 1;
    }
    const string mode = argv[3];
    const bool rgbd = mode == "rgbd";
    if (!rgbd && mode != "mono") {
        cerr << "modo deve ser mono ou rgbd" << endl;
        return 1;
    }
    const string outDir = argv[5];
    const bool realtime = argc > 6 && string(argv[6]) == "--realtime";
    const vector<Frame> frames = LoadList(argv[4], rgbd);
    if (frames.empty()) {
        cerr << "lista de quadros vazia: " << argv[4] << endl;
        return 1;
    }

    ORB_SLAM2::System slam(argv[1], argv[2], rgbd ? ORB_SLAM2::System::RGBD : ORB_SLAM2::System::MONOCULAR, false);

    ofstream log((outDir + "/frames.csv").c_str());
    log << "timestamp,tracking_state,track_ms\n" << fixed;
    for (size_t i = 0; i < frames.size(); ++i) {
        const cv::Mat image = cv::imread(frames[i].rgb, CV_LOAD_IMAGE_UNCHANGED);
        if (image.empty()) {
            cerr << "falha ao ler " << frames[i].rgb << endl;
            return 1;
        }
        const auto start = chrono::steady_clock::now();
        if (rgbd) {
            const cv::Mat depth = cv::imread(frames[i].depth, CV_LOAD_IMAGE_UNCHANGED);
            if (depth.empty()) {
                cerr << "falha ao ler " << frames[i].depth << endl;
                return 1;
            }
            slam.TrackRGBD(image, depth, frames[i].t);
        } else {
            slam.TrackMonocular(image, frames[i].t);
        }
        const double ms = chrono::duration<double, milli>(chrono::steady_clock::now() - start).count();
        log << frames[i].t << "," << slam.GetTrackingState() << "," << ms << "\n";
        if (realtime && i + 1 < frames.size()) {
            const double wait = (frames[i + 1].t - frames[i].t) * 1e3 - ms;
            if (wait > 0) this_thread::sleep_for(chrono::duration<double, milli>(wait));
        }
    }
    log.close();

    slam.Shutdown();
    slam.SaveTrajectoryTUM(outDir + "/trajectory_tum.txt");
    slam.SaveKeyFrameTrajectoryTUM(outDir + "/keyframes_tum.txt");
    return 0;
}
