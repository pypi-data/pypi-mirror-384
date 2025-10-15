// -*- C++ -*-
// AsapMPI.cpp: Interface to the MPI library.
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

#include "AsapPython.h"
#include <mpi.h>
//#include "Asap.h"
#include "Timing.h"
#include "AsapMPI.h"
#include "Exception.h"


// XXXXXX
// IMPORTANT TO-DO:  Move code into module, so assert() can be turned back into ASSERT()
// XXXXXX


static void mpi_ensure_finalized(void)
{
  int already_finalized = 1;
  int ierr = MPI_SUCCESS;

  MPI_Finalized(&already_finalized);
  if (!already_finalized)
  {
    ierr = MPI_Finalize();
  }
  if (ierr != MPI_SUCCESS)
    PyErr_SetString(PyExc_RuntimeError, "MPI_Finalize error occurred");
}


// MPI initialization
static void mpi_ensure_initialized(void)
{
  int already_initialized = 1;
  int ierr = MPI_SUCCESS;

  // Check whether MPI is already initialized
  MPI_Initialized(&already_initialized);
  if (!already_initialized)
  {
    // if not, let's initialize it
    int provided = 0;
    ierr = MPI_Init_thread(NULL, NULL,  MPI_THREAD_SERIALIZED, &provided);
    if (ierr == MPI_SUCCESS && provided >=  MPI_THREAD_SERIALIZED)
    {
      // No problem: register finalization when at Python exit
      Py_AtExit(*mpi_ensure_finalized);
    }
    else
    {
      // We have a problem: raise an exception
      char err[MPI_MAX_ERROR_STRING];
      int resultlen;
      MPI_Error_string(ierr, err, &resultlen);
      PyErr_SetString(PyExc_RuntimeError, err);
    }
  }
}



/// The Communicator provides a simplified interface to the MPI protocol.


Communicator::Communicator()
{
  mpi_ensure_initialized();
  
  MPI_Comm_dup(MPI_COMM_WORLD, &comm);
  int ok = 0;
  waiting = false;
  recvwaiting = false;
  MPI_Initialized(&ok);
  ASSERT(ok);
  nProcessors = 0;
  MPI_Comm_size(comm, &nProcessors);
  MPI_Comm_rank(comm, &nProcessor);
}

Communicator::~Communicator()
{
  MPI_Comm_free(&comm);
}
  
/// Send the buffer to another processor,
void Communicator::Send(const vector<char> &buffer, int dest)
{
  USETIMER("Communicator::Send");
#ifdef USESYNCSEND
  MPI_Ssend((void *) &buffer[0], buffer.size(), MPI_BYTE, dest,
	    7, comm);  
#else
  MPI_Send((void *) &buffer[0], buffer.size(), MPI_BYTE, dest,
	   7, comm);  
#endif /* USESYNCSEND */    
}

/// Send the buffer to another processor, but do not block sending process.
void Communicator::NonBlockingSend(const vector<char> &buffer, int dest)
{
  USETIMER("Communicator::NonBlockingSend");
  ASSERT(!waiting);
#ifdef USESYNCSEND
  MPI_Issend((void *) &buffer[0], buffer.size(), MPI_BYTE, dest, 7,
	     comm, &request);  
#else /* USESYNCSEND */
  MPI_Isend((void *) &buffer[0], buffer.size(), MPI_BYTE, dest, 7,
	    comm, &request);  
#endif /* USESYNCSEND  */
  waiting = true;
}

/// \brief Receive a message, appending it to the buffer (which is
/// resized accordingly).
void Communicator::Receive(vector<char> &buffer, int src)
{
  USETIMER("Communicator::Receive");
  MPI_Status status;
  int cnt;
  MPI_Probe(src, 7, comm, &status);
  MPI_Get_count(&status, MPI_BYTE, &cnt);
  int n = buffer.size();
  if (cnt)
    {
      // Got real data, read it.
      buffer.resize(n + cnt);
      MPI_Recv(&buffer[n], cnt, MPI_BYTE, src, 7, comm,
	       MPI_STATUS_IGNORE);
    }
  else
    {
      // Zero length message: Read it but discard it.  Apparently,
      // MPI_Recv must be passed a valid address, the end of
      // buffer[] is not OK.
      char dummy[128];  
      MPI_Recv(dummy, cnt, MPI_BYTE, src, 7, comm,
	       MPI_STATUS_IGNORE);
    }
}

/// Receive a message without blocking this process.

/// Overwrites the buffer, which must be big enough to hold the
/// message.  The corresponding WaitReceive call shrinks the buffer
/// to the size of the actual message.
void Communicator::NonBlockingReceive(vector<char> &buffer, int src)
{
  USETIMER("Communicator::NonBlockingReceive");
  ASSERT(!recvwaiting);
  MPI_Irecv(&buffer[0], buffer.size(), MPI_BYTE, src, 7, comm,
	    &recvrequest);
  recvbuffer = &buffer;
  recvwaiting = true;
}

/// \name Reduction operations.
/// They work as expected. :-)
bool Communicator::LogicalOr(bool boolean)
{
  USETIMER("Communicator::LogicalOr");
  int send = (int)boolean;
  int receive;
  MPI_Allreduce(&send, &receive, 1, MPI_INT, MPI_SUM, comm);
  return (receive > 0);
}

int Communicator::Min(int x)
{
  USETIMER("Communicator::Min");
  int min;
  MPI_Allreduce(&x, &min, 1, MPI_INT, MPI_MIN, comm);
  return min;
}

double Communicator::Min(double x)
{
  USETIMER("Communicator::Min");
  double min;
  MPI_Allreduce(&x, &min, 1, MPI_DOUBLE, MPI_MIN, comm);
  return min;
}

int Communicator::Max(int x)
{
  USETIMER("Communicator::Max");
  int max;
  MPI_Allreduce(&x, &max, 1, MPI_INT, MPI_MAX, comm);
  return max;
}

double Communicator::Max(double x)
{
  USETIMER("Communicator::Max");
  double max;
  MPI_Allreduce(&x, &max, 1, MPI_DOUBLE, MPI_MAX, comm);
  return max;
}

void Communicator::Max(vector<int> &x, vector<int> &sum)
{
  USETIMER("Communicator::Max(vector<int>)");
  sum.resize(x.size());
  MPI_Allreduce(&x[0], &sum[0], x.size(), MPI_INT, MPI_MAX, comm);
}

double Communicator::Add(double x)
{
  USETIMER("Communicator::Add(double)");
  double sum;
  MPI_Allreduce(&x, &sum, 1, MPI_DOUBLE, MPI_SUM, comm);
  return sum;
}

int Communicator::Add(int x)
{
  USETIMER("Communicator::Add(int)");
  int sum;
  MPI_Allreduce(&x, &sum, 1, MPI_INT, MPI_SUM, comm);
  return sum;
}

long Communicator::Add(long x)
{
  USETIMER("Communicator::Add(long)");
  long sum;
  MPI_Allreduce(&x, &sum, 1, MPI_LONG, MPI_SUM, comm);
  return sum;
}

unsigned long Communicator::Add(unsigned long x)
{
  USETIMER("Communicator::Add(long)");
  long sum;
  MPI_Allreduce(&x, &sum, 1, MPI_UNSIGNED_LONG, MPI_SUM, comm);
  return sum;
}

void Communicator::Add(vector<int> &x, vector<int> &sum)
{
  USETIMER("Communicator::Add(vector<int>)");
  sum.resize(x.size());
  MPI_Allreduce(&x[0], &sum[0], x.size(), MPI_INT, MPI_SUM, comm);
}

void Communicator::Add(vector<unsigned long> &x, vector<unsigned long> &sum)
{
  USETIMER("Communicator::Add(vector<long>)");
  sum.resize(x.size());
  MPI_Allreduce(&x[0], &sum[0], x.size(), MPI_UNSIGNED_LONG, MPI_SUM, comm);
}

void Communicator::Add(vector<long> &x, vector<long> &sum)
{
  USETIMER("Communicator::Add(vector<long>)");
  sum.resize(x.size());
  MPI_Allreduce(&x[0], &sum[0], x.size(), MPI_LONG, MPI_SUM, comm);
}

void Communicator::Add(vector<double> &x, vector<double> &sum)
{
  USETIMER("Communicator::Add(vector<double>)");
  sum.resize(x.size());
  MPI_Allreduce(&x[0], &sum[0], x.size(), MPI_DOUBLE, MPI_SUM, comm);
}
  
/// Wait for a nonblocking send to complete.

///
/// When Wait() returns, the send buffer may be overwritten.
void Communicator::Wait()
{
  USETIMER("Communicator::Wait");
  ASSERT(waiting);
  MPI_Wait(&request, MPI_STATUS_IGNORE);
  //    asap_mpi_wait(request);
  waiting = false;
}

/// Wait for a nonblocking receive to complete.

///
/// At return, the receive buffer contains the incoming message.
void Communicator::WaitReceive()
{
  USETIMER("Communicator::WaitReceive");
  ASSERT(recvwaiting);
  int cnt;
  MPI_Status status;
  MPI_Wait(&recvrequest, &status);
  MPI_Get_count(&status, MPI_BYTE, &cnt);
  //int cnt = asap_mpi_wait_and_count(request);
  recvbuffer->resize(cnt);
  recvwaiting = false;
}

/// All to all communication.

/// Send size integers to each process, receiving as many.  The size
/// of the sendbuffer must be size * nProcessors, the receive buffer
/// is resized to this same size.
void Communicator::AllToAll(vector<int> &sendbuf, vector<int> &recvbuf, int size)
{
  USETIMER("Communicator::AllToAll");
  ASSERT(sendbuf.size() == size * nProcessors);
  recvbuf.resize(size * nProcessors);
  MPI_Alltoall(&sendbuf[0], size, MPI_INT, &recvbuf[0], size, MPI_INT,
	       comm);
  //    asap_mpi_all_to_all_int(&sendbuf[0], &recvbuf[0], size);
}

/// AllGather.

/// Send size integers to all the processors, receive as
/// many from each processor, size*nProcessor in total.  The size of
/// the send buffer must be size, the receive buffer is resized to
/// size*nProcessors.
void Communicator::AllGather(vector<int> &sendbuf, vector<int> &recvbuf, int size)
{
  USETIMER("Communicator::AllGather");
  ASSERT(sendbuf.size() == size);
  recvbuf.resize(size * nProcessors);
  MPI_Allgather(&sendbuf[0], size, MPI_INT, &recvbuf[0], size, MPI_INT,
		comm);
  //    asap_mpi_allgather_int(&sendbuf[0], &recvbuf[0], size);
}

