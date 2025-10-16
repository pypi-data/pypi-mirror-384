#include "scheduler.h"

namespace scheduler {
std::vector<Process> fcfsScheduler(const std::vector<Process> &processes) {
  if (processes.empty()) {
    return std::vector<Process>{};
  }

  std::vector<Process> result = processes;

  std::sort(result.begin(), result.end(),
            [](const Process &a, const Process &b) {
              return a.arrivalTime < b.arrivalTime;
            });

  int currentTime = 0;

  for (int i = 0; i < result.size(); i++) {
    Process &currProcess = result[i];

    currProcess.startTime = std::max(currentTime, currProcess.arrivalTime);

    currProcess.finishTime = currProcess.startTime + currProcess.burstTime;

    currProcess.waitingTime = currProcess.startTime - currProcess.arrivalTime;
    currProcess.turnaroundTime =
        currProcess.finishTime - currProcess.arrivalTime;

    currProcess.isComplete = true;
    currProcess.remainingTime = 0;

    currentTime = currProcess.finishTime;
  };

  return result;
};

std::vector<Process> sjfScheduler(const std::vector<Process> &processes) {
  if (processes.empty()) {
    return std::vector<Process>{};
  }

  std::vector<Process> result = processes;

  std::sort(result.begin(), result.end(),
            [](const Process &a, const Process &b) {
              return a.burstTime < b.burstTime;
            });

  int currentTime = 0;

  for (int i = 0; i < result.size(); i++) {
    Process &currProcess = result[i];

    currProcess.startTime = std::max(currentTime, currProcess.arrivalTime);

    currProcess.finishTime = currProcess.startTime + currProcess.burstTime;

    currProcess.waitingTime = currProcess.startTime - currProcess.arrivalTime;
    currProcess.turnaroundTime =
        currProcess.finishTime - currProcess.arrivalTime;

    currProcess.isComplete = true;
    currProcess.remainingTime = 0;

    currentTime = currProcess.finishTime;
  };

  return result;
};

std::vector<Process> roundRobinScheduler(const std::vector<Process> &processes,
                                         int timeQuantum) {
  if (processes.empty()) {
    return std::vector<Process>{};
  }

  std::vector<Process> result = processes;
  std::queue<Process *> readyQueue;
  for (int i = 0; i < result.size(); i++) {
    readyQueue.push(&result[i]);
  }

  int currentTime = 0;

  while (!readyQueue.empty()) {
    Process *currProcess = readyQueue.front();
    readyQueue.pop();

    if (currProcess->startTime == 0) {
      currProcess->startTime = std::max(currentTime, currProcess->arrivalTime);
    }

    int executionTime = std::min(timeQuantum, currProcess->remainingTime);
    currProcess->remainingTime -= executionTime;
    currentTime += executionTime;

    currProcess->isComplete = currProcess->remainingTime <= 0;

    if (currProcess->isComplete) {

      currProcess->finishTime = currentTime;

      currProcess->turnaroundTime =
          currProcess->finishTime - currProcess->arrivalTime;

      currProcess->waitingTime =
          currProcess->turnaroundTime - currProcess->burstTime;

    } else {
      readyQueue.push(currProcess);
    }
  }

  return result;
};
} // namespace scheduler
