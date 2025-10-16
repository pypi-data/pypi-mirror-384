#pragma once
#include <algorithm>
#include <iostream>
#include <queue>
#include <string>
#include <vector>
namespace scheduler {

struct Process {
  int pid;
  int arrivalTime;
  int burstTime;

  int startTime;
  int finishTime;
  int waitingTime;
  int turnaroundTime;
  int remainingTime;
  bool isComplete;

  Process(int id, int arrival, int burst)
      : pid(id), arrivalTime(arrival), burstTime(burst), startTime(0),
        finishTime(0), waitingTime(0), turnaroundTime(0), remainingTime(burst),
        isComplete(false) {};
};

std::vector<Process> fcfsScheduler(const std::vector<Process> &processes);

std::vector<Process> sjfScheduler(const std::vector<Process> &processes);

std::vector<Process> roundRobinScheduler(const std::vector<Process> &processes,
                                         int timeQuantum);
} // namespace scheduler