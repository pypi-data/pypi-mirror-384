// -*- C++ -*-
// AsapMPI.h: Interface to the MPI library.
//
// Copyright (C) 2001-2011 Jakob Schiotz and Center for Individual
// Nanoparticle Functionality, Department of Physics, Technical
// University of Denmark.  Email: schiotz@fysik.dtu.dk
//
// This file is part of Asap version 3.
//
// This program is free software: you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public License
// version 3 as published by the Free Software Foundation.  Permission
// to use other versions of the GNU Lesser General Public License may
// granted by Jakob Schiotz or the head of department of the
// Department of Physics, Technical University of Denmark, as
// described in section 14 of the GNU General Public License.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// and the GNU Lesser Public License along with this program.  If not,
// see <http://www.gnu.org/licenses/>.


#ifndef _ASAP_MPI_H
#define _ASAP_MPI_H

#include <mpi.h>
#include <vector>
using std::vector;
#include <string>
using std::string;
#include "Asap.h"

namespace ASAPSPACE {

// XXXXXX
// IMPORTANT TO-DO:  Move code into module, so assert() can be turned back into ASSERT()
// XXXXXX

/// The Communicator provides a simplified interface to the MPI protocol.
class Communicator
{
public:
  Communicator();

  ~Communicator();
  
  /// Get the number of processors in the simulation.
  inline int GetNumberOfProcessors() const {return nProcessors;}
  /// Get the number of this processor (the "rank" in the MPI communicator).
  inline int GetProcessorNumber() const {return nProcessor;}

  /// Send the buffer to another processor,
  void Send(const vector<char> &buffer, int dest);

  /// Send the buffer to another processor, but do not block sending process.
  void NonBlockingSend(const vector<char> &buffer, int dest);
  
  /// \brief Receive a message, appending it to the buffer (which is
  /// resized accordingly).
  void Receive(vector<char> &buffer, int src);

  /// Receive a message without blocking this process.

  /// Overwrites the buffer, which must be big enough to hold the
  /// message.  The corresponding WaitReceive call shrinks the buffer
  /// to the size of the actual message.
  void NonBlockingReceive(vector<char> &buffer, int src);

  /// \name Reduction operations.
  /// They work as expected. :-)

  //@{
  bool LogicalOr(bool boolean);
    
  int Min(int x);

  double Min(double x);
  
  int Max(int x);
  
  double Max(double x);
  
  void Max(vector<int> &x, vector<int> &sum);
    
  double Add(double x);

  int Add(int x);
  
  long Add(long x);

  unsigned long Add(unsigned long x);

  void Add(vector<int> &x, vector<int> &sum);
  
  void Add(vector<long> &x, vector<long> &sum);

  void Add(vector<unsigned long> &x, vector<unsigned long> &sum);

  void Add(vector<double> &x, vector<double> &sum);
  //@}
  
  /// Wait for a nonblocking send to complete.

  ///
  /// When Wait() returns, the send buffer may be overwritten.
  void Wait();

  /// Wait for a nonblocking receive to complete.

  ///
  /// At return, the receive buffer contains the incoming message.
  void WaitReceive();
  
  /// All to all communication.

  /// Send size integers to each process, receiving as many.  The size
  /// of the sendbuffer must be size * nProcessors, the receive buffer
  /// is resized to this same size.
  void AllToAll(vector<int> &sendbuf, vector<int> &recvbuf, int size);

  /// AllGather.

  /// Send size integers to all the processors, receive as
  /// many from each processor, size*nProcessor in total.  The size of
  /// the send buffer must be size, the receive buffer is resized to
  /// size*nProcessors.
  void AllGather(vector<int> &sendbuf, vector<int> &recvbuf, int size);

  // Temporary - remove after merging this with the Python object
  inline MPI_Comm get_mpi_comm() {
    return comm;
  }
    
private:
  MPI_Comm comm;     ///< Communicator object
  bool waiting;      ///< Waiting for nonblocking send
  bool recvwaiting;  ///< Waiting for nonblocking receive
  int nProcessor;    ///< The number of this processor
  int nProcessors;   ///< The total number of processors in the simulation.
  MPI_Request request;     ///< For nonblocking send.
  MPI_Request recvrequest; ///< For nonblocking recv.
  vector<char> *recvbuffer; ///< The buffer used in nonblocking recv.
  // string filename;   // Not used?
};

} // end namespace

#endif//  _ASAP_MPI_H
