/*
 * Copyright(c) 2021 to 2022 ZettaScale Technology and others
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License v. 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0, or the Eclipse Distribution License
 * v. 1.0 which is available at
 * http://www.eclipse.org/org/documents/edl-v10.php.
 *
 * SPDX-License-Identifier: EPL-2.0 OR BSD-3-Clause
 */

#ifndef PYSERTYPE_H
#define PYSERTYPE_H

#define PY_SSIZE_T_CLEAN
#include <Python.h>

extern const struct dds_cdrstream_allocator cdrstream_allocator;

PyMODINIT_FUNC PyInit__clayer(void);

#endif // PYSERTYPE_H
