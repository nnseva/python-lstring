/*-----------------------------------------------------------------------------
| Typed wrapper for cppy::ptr
|----------------------------------------------------------------------------*/
#pragma once

#include <cppy/ptr.h>


template <typename T>
class tptr
{
public:
	// Default constructor
	tptr() : m_ptr()
	{
	}

	// Constructor from PyObject*
	tptr( PyObject* ob, bool incref = false ) : m_ptr( ob, incref )
	{
	}

	// Constructor from T*
	tptr( T* ob, bool incref = false ) : m_ptr( reinterpret_cast<PyObject*>(ob), incref )
	{
	}

	// Copy constructor
	tptr( const tptr& other ) : m_ptr( other.m_ptr )
	{
	}

	// Copy assignment
	tptr& operator=( const tptr& other )
	{
		m_ptr = other.m_ptr;
		return *this;
	}

	// Access to wrapped cppy::ptr
	cppy::ptr& ptr()
	{
		return m_ptr;
	}

	const cppy::ptr& ptr() const
	{
		return m_ptr;
	}

	// Typed access
	T* get() const
	{
		return reinterpret_cast<T*>( m_ptr.get() );
	}

	// Release ownership
	T* release()
	{
		return reinterpret_cast<T*>( m_ptr.release() );
	}

	// Operator overloads
	T* operator->() const
	{
		return get();
	}

	T& operator*() const
	{
		return *get();
	}

	explicit operator bool() const
	{
		return m_ptr.get() != nullptr;
	}

private:
	cppy::ptr m_ptr;
};
