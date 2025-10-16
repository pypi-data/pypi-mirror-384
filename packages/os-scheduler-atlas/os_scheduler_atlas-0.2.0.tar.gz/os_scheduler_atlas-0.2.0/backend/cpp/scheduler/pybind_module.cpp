#include "scheduler.h"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;
using namespace scheduler;

Process dict_to_process(py::dict proc_dict) {
  return Process{proc_dict["pid"].cast<int>(),
                 proc_dict["arrival_time"].cast<int>(),
                 proc_dict["burst_time"].cast<int>()};
}

py::dict process_to_dict(const Process &process) {
  py::dict result;

  result["pid"] = process.pid;
  result["arrival_time"] = process.arrivalTime;
  result["burst_time"] = process.burstTime;
  result["waiting_time"] = process.waitingTime;
  result["turn_around_time"] = process.turnaroundTime;
  result["finish_time"] = process.finishTime;
  result["remaining_time"] = process.remainingTime;
  result["is_complete"] = process.isComplete;

  return result;
}

py::list fcfs_scheduler_wrapper(py::list process_list) {
  std::vector<Process> processes;

  for (const auto &process : process_list) {
    Process convertedProcess = dict_to_process(process.cast<py::dict>());
    processes.push_back(convertedProcess);
  }

  std::vector<Process> result = fcfsScheduler(processes);

  py::list result_process_list;

  for (const auto &process : result) {
    py::dict convertedProcess = process_to_dict(process);
    result_process_list.append(convertedProcess);
  }

  return result_process_list;
}

py::list sjf_scheduler_wrapper(py::list process_list) {
  std::vector<Process> processes;

  for (const auto &process : process_list) {
    Process convertedProcess = dict_to_process(process.cast<py::dict>());
    processes.push_back(convertedProcess);
  }

  std::vector<Process> result = sjfScheduler(processes);

  py::list result_process_list;

  for (const auto &process : result) {
    py::dict convertedProcess = process_to_dict(process);
    result_process_list.append(convertedProcess);
  }

  return result_process_list;
}

py::list round_robin_scheduler_wrapper(py::list process_list,
                                       int time_quantum) {
  std::vector<Process> processes;

  for (const auto &process : process_list) {
    Process convertedProcess = dict_to_process(process.cast<py::dict>());
    processes.push_back(convertedProcess);
  }

  std::vector<Process> result = roundRobinScheduler(processes, time_quantum);

  py::list result_process_list;

  for (const auto &process : result) {
    py::dict convertedProcess = process_to_dict(process);
    result_process_list.append(convertedProcess);
  }

  return result_process_list;
}

PYBIND11_MODULE(scheduler_cpp, m) {
  m.doc() = "OS Scheduling Algorithms";

  m.def("fcfs_scheduler", &fcfs_scheduler_wrapper,
        "First Come First Served scheduling algorithm", py::arg("processes"));

  m.def("sjf_scheduler", &sjf_scheduler_wrapper,
        "Shortest Job First scheduling algorithm", py::arg("processes"));

  m.def("round_robin_scheduler", &round_robin_scheduler_wrapper,
        "Round Robin scheduling algorithm", py::arg("processes"),
        py::arg("time_quantum"));
}