======
Theory
======

This section will contain the theoretical background of the code. It will be
divided into several subsections, each of which will contain a brief
introduction to the topic, followed by a more detailed explanation of the
relevant concepts.

Introduction to Symmetry
========================

Symmetry is a fundamental concept in physics and mathematics. It is a property of an
object that remains unchanged under some transformation. For example, a square has
rotational symmetry of order 4, because it looks the same after a 90 degree rotation.
Symmetry can be described in terms of a group of transformations that leave the object
invariant. This group is called the symmetry group of the object. There are several
types of symmetry operations that are often encountered in physics, such as rotations,
reflections, and translations. These operations can be combined to form more complex
symmetry operations.

There are two main types of symmetry operations associated with point groups: rotations
and reflections. Inversion can be considered as a special case of reflection, while
rotoreflections can be constructed using combination of rotations and inversions. In
space groups in addition to the above-mentioned symmetry elements we also have
translational symmetry. This symmetry can be combined with elements of point group
symmetry to obtain new unique type of symmetry operations such as screw axes (rotation +
translation) and glide planes (reflections + translations). Since PGOP computes only
point group symmetry we shall focus only on point group symmetry.


Symmetry operations in point groups
-----------------------------------

Rotations are defined by the axis of rotation and the angle of rotation.  Various
representations of rotations exist, each with distinct advantages and disadvantages. In
PGOP, we primarily use the Euler angle representation in the zyz convention because the
relevant literature often adopts it :cite:`Altmann_WignerD`. A rotation operation is
written as :math:`\hat{C}_{nz}`, where :math:`n` represents the order of rotation and
the second letter indicates the rotation axis. Other axes besides :math:`x`, :math:`y`,
or :math:`z` can be used. If the operation is written without an explicit rotation axis,
such as :math:`\hat{C}_n`, it denotes the main rotation axis (aligned with the rotation
axis of the highest rotation order), typically taken to be the :math:`z` axis. The angle
of rotation (:math:`\theta`) can be computed from the order :math:`n` using the formula:
:math:`\theta = 2\pi/n = 360^\circ / n`. Multiple consecutive rotations are often
applied in group theory and are written using power notation: :math:`\hat{C}_n^m`. This
notation means that the operation :math:`\hat{C}_n` is applied :math:`m` times in
succession.

Reflections are defined by the plane of reflection. Reflections are a type of symmetry
operation that flips the object across the plane of reflection. Reflections cannot be
represented as rotations, or combination of rotations in a general sense. Reflections
can be represented as inversion followed by a rotation of 180 degrees
:cite:`Altmann_WignerD`:

.. math::
    \hat{\sigma}_{xy} = \hat{i} \hat{C}_{2z} \\
    \hat{\sigma}_h = \hat{i} \hat{C}_2

where :math:`\hat{i}` is the inversion operator and :math:`\hat{C}_2(z)` is the two fold
rotation around :math:`z` axis. The reflection plane is always perpendicular to the axis
of rotation obtained by the above formula.

Inversion is a symmetry operation that flips the object across the center of inversion.
It can be shown that inversion can be represented by an application of 3 orthogonal
reflections :cite:`engel2021point`:

.. math::
    \hat{i} = \hat{\sigma}_{yz} \hat{\sigma}_{xz} \hat{\sigma}_{xy}

Rotoreflections are a combination of rotations and reflections, sometimes called
improper rotations. They are a type of symmetry operation that combines rotation and
reflection. Thus, by definition, we can write :cite:`Altmann_WignerD`:

.. math::
    \hat{S}_n = \hat{\sigma}_h {\hat{C}_n} = \hat{\sigma}_{xy} {\hat{C}_n}

where :math:`\hat{\sigma}_h=\hat{\sigma}_{xy}` is the reflection operator perpendicular
to the axis of rotation (:math:`z`).

Some useful equivalency relations for rotoreflections and their powers used in PGOP code
can be found in work by Drago :cite:`drago1992`.


Group theory
------------

In group theory, sets with an operation under certain constraints (operation must be
associative, and have an identity element, and every element of the set must have an inverse) are
called groups. When studying symmetry groups, we usually consider groups under operation
of composition. The elements of the group are symmetry operations. Elements of the group
can act on many different objects such as Euclidian space, or physical or other
geometrical objects built from such an object (for example shapes or points). Euclidian
(or other types of spaces) can often be described as vector spaces.

Another important aspect of the group is the group action. First, let's consider a
general action of some element of group :math:`G`. Let :math:`G` be a group under
composition. Consider an action of an element of group :math:`G`, say operator :math:`g`
on some function :math:`f`. The action of :math:`g` on :math:`f` is just the composition
of :math:`g` on :math:`f`. If we assume that :math:`G` is a symmetry group, then the
interpretation of this composition is that action of :math:`g` symmetrizes the function
:math:`f` according to symmetry operator :math:`g`. Similarly, we can also apply a group
action of the group :math:`G` onto some function :math:`f`. The group action is
symmetrization under all the elements (symmetry operators) of the group. If we assume
that :math:`G` is a finite point group, the group action is given by the following
formula:

.. math::
    f_G = \frac{1}{|G|} \sum_{g \in G} g \cdot f,

where :math:`|G|` is the order of the group (number of elements of :math:`G`).

When group action acts on a vector space (or any other operator for that matter) we call
this a representation. Notice that choosing a representation enables us to actually
numerically write out the operator in a matrix form. In our case the point group
symmetry action operation can be represented as a matrix.


Symmetry Point groups
~~~~~~~~~~~~~~~~~~~~~

Infinitely many point groups exist. Point groups are divided into categories according
to the elements they contain and include the following:

- Cyclic groups (starting with Schoenflies symbol C), which contain operations
  related to a rotation of a given degree :math:`n`
- Rotoreflection groups (S), which contain rotoreflection operations
- Dihedral groups (D), which contain operations related to rotation of a given degree
  n and reflection across a plane perpendicular to the rotation axis
- Cubic/polyhedral groups (O, T, I), which contain symmetry operations related to
  important polyhedra in 3D space

We give an overview of important point groups for materials science and
crystallography below, with some remarks on notation and nomenclature.

With :math:`\hat{\sigma}_h` we label the reflection which is perpendicular (orthogonal)
to the principal symmetry axis. On the other hand :math:`\hat{\sigma}_v` is the
reflection parallel to the principal symmetry axis. There are multiple choices
one can make with parallel reflection, such as in the :math:`zx` or :math:`zy` plane.
With :math:`\hat{\sigma}_d` we usually label reflections parallel to the principal axis
that are not :math:`zx` or :math:`zy`.

The group operations are taken from the following `link
<http://symmetry.constructor.university/cgi-bin/group.cgi?group=1>`_. We follow the
nomenclature found in :cite:`ezra` and :cite:`Altmann_semidirect`. In addition to that,
we shall adopt a nomenclature in which :math:`\hat{\sigma}_h = \hat{\sigma}_{xy}` is the
only horizontal reflection plane, while :math:`\hat{\sigma}_{v}` can be any reflection
plane containing principal axis of symmetry in :math:`z` direction. Note that some other
sources (such as :cite:`ezra`) would for some of these reflection planes use
:math:`\hat{\sigma}^{'}`. The designation :math:`\hat{\sigma}_d` denotes a subset of
reflections :math:`\hat{\sigma}_{v}` which also bisect the angle between the twofold
axes perpendicular to the principal symmetry axis(:math:`z`). We opt to not use the
designation :math:`\hat{\sigma}_d`. The definitions for specific operations are also
given `here
<https://web.archive.org/web/20120813130005/http://newton.ex.ac.uk/research/qsystems/people/goss/symmetry/CharacterTables.html>`_.

Many operations in the table contain a power. The power is to be read as applying the
same operation multiple times. For example :math:`{\hat{C}_2}^2` applies
:math:`\hat{C}_2` operation twice. The elements of groups :math:`S_n` for odd values of
:math:`n` are also given in :cite:`drago1992`.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Point Group
     - Symmetry Operations
   * - :math:`C_1`
     - :math:`\hat{E}`
   * - :math:`C_s`
     - :math:`\hat{E}`, :math:`\hat{\sigma}_v`
   * - :math:`C_h`
     - :math:`\hat{E}`, :math:`\hat{\sigma}_h`
   * - :math:`C_i`
     - :math:`\hat{E}`, :math:`\hat{i}`
   * - :math:`C_n`
     - :math:`\hat{E}`, :math:`\hat{C}_n`, :math:`{\hat{C}_n}^2`, ... :math:`{\hat{C}_n}^{n-1}`
   * - :math:`C_{nh}`, :math:`n` is even
     - :math:`\hat{E}`, :math:`\hat{C}_n`, :math:`{\hat{C}_n}^2`, ... :math:`{\hat{C}_n}^{n-1}`, :math:`\hat{\sigma}_h`, :math:`\hat{S}_n`, :math:`{\hat{S}_n}^3`, ... :math:`{\hat{S}_n}^{n-1}`
   * - :math:`C_{nh}`, :math:`n` is odd
     - :math:`\hat{E}`, :math:`\hat{C}_n`, :math:`{\hat{C}_n}^2`, ... :math:`{\hat{C}_n}^{n-1}`, :math:`\hat{\sigma}_h`, :math:`\hat{S}_n`, :math:`{\hat{S}_n}^3`, ... :math:`{\hat{S}_n}^{2n-1}`
   * - :math:`C_{nv}`
     - :math:`\hat{E}`, :math:`\hat{C}_n`, :math:`{\hat{C}_n}^2`, ... :math:`{\hat{C}_n}^{n-1}`, :math:`n \hat{\sigma}_v`
   * - :math:`D_n`
     - :math:`\hat{E}`, :math:`\hat{C}_n`, :math:`{\hat{C}_n}^2`, ... :math:`{\hat{C}_n}^{n-1}`, :math:`n \hat{C}_2^{'}`
   * - :math:`D_{nh}`
     - :math:`\hat{E}`, :math:`\hat{C}_n`, :math:`{\hat{C}_n}^2`, ... :math:`{\hat{C}_n}^{n-1}`, :math:`n \hat{C}_2^{'}`, :math:`\hat{\sigma}_h`, :math:`\hat{C}_n \hat{\sigma}_h`, :math:`{\hat{C}_n}^2 \hat{\sigma}_h`, ... :math:`{\hat{C}_n}^{n-1} \hat{\sigma}_h`, :math:`n\hat{\sigma}_v`
   * - :math:`D_{nd}` (sometimes called :math:`D_{nv}`)
     - :math:`\hat{E}`, :math:`\hat{C}_n`, :math:`{\hat{C}_n}^2`, ... :math:`{\hat{C}_n}^{n-1}`, :math:`n \hat{C}_2^{'}`, :math:`\hat{S}_{2n}`, :math:`{\hat{S}_{2n}}^3`, ... :math:`{\hat{S}_{2n}}^{2n-1}`, :math:`n\hat{\sigma}_v`
   * - :math:`S_{n}`, :math:`n` is even
     - :math:`\hat{E}`, :math:`\hat{S}_{n}`, :math:`{\hat{S}_{n}}^2`, ... :math:`{\hat{S}_{n}}^{n-1}`
   * - :math:`S_{n}`, :math:`n` is odd
     - :math:`\hat{E}`, :math:`\hat{S}_{n}`, :math:`{\hat{S}_{n}}^2`, ... :math:`{\hat{S}_{n}}^{2n-1}`
   * - :math:`T`
     - :math:`\hat{E}`, :math:`4 \hat{C}_3`, :math:`4 {\hat{C}_3}^2`, :math:`3 \hat{C}_2`
   * - :math:`T_h`
     - :math:`\hat{E}`, :math:`4 \hat{C}_3`, :math:`4 {\hat{C}_3}^2`, :math:`3\hat{C}_2`, :math:`\hat{i}`, :math:`3 \hat{\sigma}_h`, :math:`4 \hat{S}_6`, :math:`4 {\hat{S}_6}^5`
   * - :math:`T_d`
     - :math:`\hat{E}`, :math:`8 \hat{C}_3`, :math:`3 \hat{C}_2`, :math:`6 \hat{\sigma}_v`, :math:`6\hat{S}_4`
   * - :math:`O`
     - :math:`\hat{E}`, :math:`6 \hat{C}_4`, :math:`8 \hat{C}_3`, :math:`9 \hat{C}_2`
   * - :math:`O_h`
     - :math:`\hat{E}`, :math:`6 \hat{C}_4`, :math:`8 \hat{C}_3`, :math:`9 \hat{C}_2`, :math:`3 \hat{\sigma}_h`, :math:`6\hat{\sigma}_v`, :math:`\hat{i}`, :math:`8\hat{S}_6`, :math:`6\hat{S}_4`
   * - :math:`I`
     - :math:`\hat{E}`, :math:`12 \hat{C}_5`, :math:`12 {\hat{C}_5}^2`, :math:`20\hat{C}_3`, :math:`15 \hat{C}_2`
   * - :math:`I_h`
     - :math:`\hat{E}`, :math:`12 \hat{C}_5`, :math:`12 {\hat{C}_5}^2`, :math:`20\hat{C}_3`, :math:`15 \hat{C}_2`, :math:`15\hat{\sigma}_v`, :math:`\hat{i}`, :math:`12\hat{S}_{10}`, :math:`12{\hat{S}_{10}}^3`, :math:`20\hat{S}_6`

Notes on the table:

* :math:`C_{nv}`: each :math:`\hat{\sigma}_v` is a reflection plane containing the
  principal axis of symmetry starting with :math:`\hat{\sigma}_{yz}`, and the rest
  are successive rotations of the plane around :math:`z` axis by :math:`\frac{\pi}{n}`.
* All dihedral groups (:math:`D_n`, :math:`D_{nh}`, :math:`D_{nd}`): each
  :math:`\hat{C}_2^{'}` is perpendicular to the principal axis of symmetry starting with
  :math:`\hat{C}_{2x}` and rest are successive rotation of this plane by
  :math:`\frac{2\pi}{n}`.
* :math:`D_{nh}`: each :math:`\hat{\sigma}_v` is a reflection plane parallel to
  both principal (:math:`z`) and each :math:`\hat{C}_2^{'}` axis.
* :math:`D_{nh}`: the :math:`\hat{C}_n^m \hat{\sigma}_h` evaluate to different
  :math:`\hat{S}_n` or :math:`\hat{S}_{n/2}` operator powers, see :cite:`bishop1993`
  for more details.
* :math:`D_{nd}`: each :math:`\hat{\sigma}_d` is a reflection plane parallel to
  the principal axis of symmetry (:math:`z`) and also contains the vector which
  bisects two neighboring :math:`\hat{C}_2^{'}` axes of symmetry.
* All tetrahedral groups (:math:`T`, :math:`T_h`, :math:`T_d`): see
  :cite:`Altmann_WignerD` for specific proper rotations and also see Hurwitz
  quaternions.
* All octahedral groups (:math:`O`, :math:`O_h`): see Lipshitz and Hurwitz quaternions
  for specific proper rotations
* All icosahedral groups (:math:`I`, :math:`I_h`): see Hurwitz and icosian quaternions
  for specific proper rotations

Several point groups from the table above are equivalent. For more information see `this
link <https://en.wikipedia.org/wiki/Schoenflies_notation#Point_groups>`_. In PGOP all
point groups were constructed from their operations given in the above table.

Introduction to Point Group Order Parameter (PGOP)
==================================================

The main purpose of PGOP is to quantify the degree of symmetry order of a local
distribution of positions with respect to a given point and a given point group. To do
this effectively we have to make sure we can measure symmetry in a continuous way. This
is tricky because symmetry is often defined as a binary property. A configuration can
either be symmetric or not. The main idea of PGOP is to turn this into a continuous
measure by comparing how far a given configuration is from a symmetrized version of the
same configuration. This symmetrization can simply be obtained by applying the group
action. We provide several ways to do this. Bond orientational order symmetry order
parameter (BOOSOP) is based on an old implementation in which neighbor positions are
projected onto a unit sphere, replaced with fisher distribution (gaussian on a sphere)
and then symmetrized with respect to the point group of interest, by applying the Wigner
D matrix of a group action operation. The comparison of the two distributions is done
by computing the normalized inner product between the two spherical harmonic expansions.
In a newer implementation named PGOP-BOOD (Point Group Order Parameter of Bond
Orientational Order Diagram) we use the same idea, but instead of computing the
spherical harmonic expansion of the fisher distributions, we consider the overlaps
between fisher functions of the symmetrized configuration with the original
configuration. We also support a version which quantifies full point group symmetry
(called simply PGOP) in which we don't project the neighbors onto the unit sphere, but
rather consider the full 3D positions of the neighbors which are now replaced by 3D
gaussian distribution. The distance between the symmetrized and original configurations
are calculated by computing the overlap between the two gaussians. The main difference
here is that in the PGOP version is in the symmetrization procedure. In PGOP we cannot
apply the group action at once, but rather each symmetry operation has to be applied to
each neighbor separately, and results of the overlaps are averaged over all neighbors
and symmetry operations. This is because the representation of the group action is
different in Cartesian (or spherical harmonic space) vs the function space in which we
expanded the configurations in BOOSOP.

Point group order parameter
---------------------------

The point group order parameter (PGOP) is a measure of the degree of symmetry of a
particle configuration with respect to a given point in space (which could be a position
of another particle or not) and a given point group. There are 3 main steps of this
procedure. First, starting configuration is symmetrized with respect to a symmetry
operation from the point group. Next, for each symemtrized position we compute the
maximal overlap between a normalized gaussian centered at that symmetrized position and
any other normalized gaussian centered at original positions. This is done for all
positions in the set of symmetrized positions and for all symmetry operations. The final
value of the order parameter is just the average of all these overlaps. The last step is to
find the orientation of the principal symmetry axis of the point group which maximizes
the value of the order parameter. This can be done in several ways and the code supports
several optimization procedures. We support two flavors of PGOP: one in which the
point group symmetry of bond orientational order is measured (PGOP-BOOD) and one in which
the full point group symmetry is measured (PGOP). The main free parameter of the method
is the choice of gaussian width. The width determines the sensitivity of the order
parameter. In the limit of :math:`\sigma \rightarrow 0` the order parameter will be 1
for perfect symmetry and 0 for no symmetry, so binary. The choice of the width also
influences the convergence of the optimization procedure. Higher widths usually converge
faster and easier. Thus one has to be careful when choosing the width. The width can be
chosen on a per particle basis, but this is not recommended.

Calculation of overlap
~~~~~~~~~~~~~~~~~~~~~~
To compute the overlap between two gaussians we use the Bhattacharyya
coefficient :cite:`bhattacharyya_measure_1946` :cite:`bhattacharyya_measure_1943`. The
formula for the Bhattacharyya coefficient is for PGOP in Cartesian representation
between two gaussians :math:`G_1` and :math:`G_2` is given by :cite:`kashyap_perfect_2019`:

.. math::
  \mathrm{BC}(G_1,G_2)= \left(\frac{2\sigma_1\sigma_2}{\sqrt{\sigma_1^2+\sigma_2^2}}\right)^{3/2} \exp{-\frac{\left|\vec{r}_1-\vec{r}_2\right|^2}{4\left(\sigma_1^2+\sigma_2^2\right)}}.

Using the formula for the Bhattacharyya coefficient for PGOP-BOOD, we first do a coordinate
transformation to spherical coordinates and then compute the overlap between two fisher
distributions:

.. math::
      \mathrm{BC}(P_1,P_2) = 2 \sqrt{\frac{\kappa_1\kappa_2}{\sinh{\kappa_1}\sinh{\kappa_2}}} \frac{\sinh{\frac{\sqrt{\kappa_1^2+\kappa_2^2+2\kappa_1\kappa_2\vec{r}_1\times\vec{r}_2}}{2}}}{\sqrt{\kappa_1^2+\kappa_2^2+2\kappa_1\kappa_2\vec{r}_1\times\vec{r}_2}}.

We always use normalized distributions for the calculation of the Bhattacharyya coefficient
to normalize the order parameter to the range [0,1].


Cartesian representation of symmetry operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Below, we provide an overview of the key symmetry operations and their matrix representations for 3D Cartesian representation.

The identity matrix :math:`\mathbf{I}` represents the identity operation
:math:`\hat{E}`, which leaves all points unchanged. It is given by:

.. math::
  \hat{E} = \mathbf{I} =
  \begin{pmatrix}
  1 & 0 & 0 \\
  0 & 1 & 0 \\
  0 & 0 & 1
  \end{pmatrix}.

In three-dimensional space, a rotation matrix :math:`\hat{C}_n` can be constructed for a
rotation by an angle :math:`\theta` about an axis defined by a unit vector
:math:`\vec{u} = (u_x, u_y, u_z)`. Other representations that are more computationally
efficient do exist, such as quaternions, but we shall use the matrix representation for
its simplicity and compatibility with other symmetry operations. The general form of the
rotation matrix in Cartesian coordinates is given by:

.. math::
  \hat{C}_n(\theta=2\pi/n, \vec{u}) =
  \begin{pmatrix}
  \cos\theta + u_x^2(1 - \cos\theta) & u_x u_y (1 - \cos\theta) - u_z \sin\theta & u_x u_z (1 - \cos\theta) + u_y \sin\theta \\
  u_y u_x (1 - \cos\theta) + u_z \sin\theta & \cos\theta + u_y^2(1 - \cos\theta) & u_y u_z (1 - \cos\theta) - u_x \sin\theta \\
  u_z u_x (1 - \cos\theta) - u_y \sin\theta & u_z u_y (1 - \cos\theta) + u_x \sin\theta & \cos\theta + u_z^2(1 - \cos\theta)
  \end{pmatrix}.

We use the implementation provided by SciPy to compute the rotation matrix from
angle-axis representation or Euler angles in zyz notation :cite:`virtanen_scipy_2020`.

Inversion is a symmetry operation that maps each point to its opposite point with
respect to the origin. The inversion matrix :math:`\hat{i}` in Cartesian representation
is simply:

.. math::
  \hat{i} = -\mathbf{I} =
  \begin{pmatrix}
  -1 & 0 & 0 \\
  0 & -1 & 0 \\
  0 & 0 & -1
  \end{pmatrix}.

The reflection matrix :math:`\vec{\sigma}` for a reflection across a plane with a normal
vector :math:`\vec{n} = (n_x, n_y, n_z)` is given by:

.. math::
  \vec{\sigma} = \hat{i} \hat{C}_2 (\theta=\pi, \vec{n}).

Rotoreflections are combinations of rotations and reflections and can be represented by
the composition of reflection and rotation. A rotoreflection matrix :math:`\vec{S}_n`
for a rotation by an angle :math:`\theta=2\pi/n` about an axis :math:`\vec{u}` followed
by a reflection across a plane :math:`\hat{\sigma}` perpendicular to :math:`\vec{u}` can
be constructed as:

.. math::
  \vec{S}_n (\theta=2\pi/n, \vec{u}) = \hat{\sigma} (\vec{u}) \hat{C}_n(\theta=2\pi/n, \vec{u}),

where :math:`\hat{\sigma}` is the reflection matrix across the plane perpendicular to
the axis of rotation and :math:`\hat{C}_n` is the rotation matrix.



Bond orientational order symmetry order parameter
-------------------------------------------------

BOOSOP is used to determine the symmetry of the bond orientational order diagram (BOOD).
BOOD is a tool for visually analyzing and interpreting the bond orientational order.
Bond orientational order describes relative arrangement of neighbors of a central
particle. An intuitive way to think about it is to consider different types of
coordination environments. For example, octahedral orientational order and tetrahedral
orientational order are different types of bond orientational order. The neighbors have
to be computed with respect to some reference in space. This point in space can belong
to a particle location (which is usually the case), but doesn't have to. Thus, BOOSOP does
not measure the point group symmetry of this chosen point in space, but rather the point
group symmetry of projections of these points to a unit sphere (the BOOD). It is
important to note that BOOSOP is not a measurement of Wyckoff site symmetry or
crystalline point group symmetry. To compute a crystalline point group symmetry,BOOSOP
should be measured at the location of the general position. The general position refers to a
point in a crystal that does not transform with any symmetry operations.
Understanding this, a big strength of BOOSOP comes from its ability to interpret
symmetry on a continuous scale, instead of a binary property. Symmetry is typically
defined as a binary relation between two objects that are the same under some
transformation.

BOOSOP results are given on a scale from 0 to 1, with 1 meaning perfect symmetry of
the given point group, and 0 meaning no match for that symmetry. In real systems,
we do not expect to see values of 0 and 1. By approaching symmetry measurements in
this way, we can use BOOSOP in cases in which we want to study changes in the local
structure of a crystal as it is formed.

The calculation of BOOSOP can be broken down into 4 main parts:

1. The construction of a Bond Orientational Order Diagram (BOOD)
2. The spherical harmonics expansion of the BOOD
3. The construction of a symmetrized BOOD with respect to the point group of interest
4. The comparison of the two BOODS

Step 1: Constructing the BOOD of the System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To understand BOOSOP, it is important to first consider a Bond Orientational Order
Diagram (BOOD). A BOOD can be thought of as a projection of the relative positions of
particle neighbors projected onto a unit sphere.
This is useful as it provides a way to examine the local environment that a particle
is experiencing. For constructing a BOOD, the determination of nearest neighbors is
important, as this can change the results. This will also affect the results of BOOSOP
calculations. While the distance between particles may be important for determining
if they are neighbors, it is not part of the BOOD.

Step 2: Spherical Harmonics Expansion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Now that we understand BOODs, let's talk about spherical harmonics. In the case of
BOOSOP, Spherical Harmonics are particularly useful as they provide a complete basis
in the space of functions on the sphere, thereby allowing spherical functions to be
written as linear combinations of these basis functions. In BOOSOP, we construct a
Spherical Harmonics expansion of the BOOD of our system. In order to do this, we
first identify the particle positions relative to a central point. We then convert
these into spherical harmonics, compute these for each bond, and then sum these
spherical harmonics.

Steps 3 and 4: Construction of the symmetrized BOOD and BOOD Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Next, we have to symmetrize the constructed BOOD. To do this, we simply apply the Wigner
D matrix of a group action operation of a given point group symmetry on the computed
BOOD. To quantify if the symmetrized BOOD is different from the initially constructed
BOOD, we compute the normalized inner product between the two spherical harmonic
expansions that are defined by the initial and symmetrized BOOD. Before computing the
final value of BOOSOP, we have to find the rotation which minimizes this inner product.
If we take the BOOD of our system, we want to find where it best matches the symmetrized
one. This is done using a brute force optimization plus gradient descent. The search is
done over all the rotations in 3D space, as described by the 3D rotation group, SO(3).

At this point, it is important to note how the actions of symmetry are represented.
For this, we use Wigner D matrices. These matrices provide a way to mathematically
express these operations with finite-dimensional matrices.

Wigner D matrices
-----------------
Symmetry operations can be represented as matrices acting on a vector space. One approach for
this is to use Wigner D matrices, which represent symmetry operations in the space spanned by
spherical harmonics.


Matrix representation of symmetry operations for spherical harmonics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A single Wigner :math:`D` matrix is defined for a given symmetry operation and a given :math:`l`, which
is the degree of the spherical harmonic. The Wigner :math:`D` matrix is a square matrix of size
:math:`2l+1`. The indices of the matrix are often written as :math:`m` and :math:`m'`
and they range from :math:`-l` to :math:`l`. The vectors which these matrices operate on
are coefficients for a spherical harmonic given by :math:`l` and :math:`m` (each vector
element is different :math:`m`).

A single Wigner :math:`D` matrix is defined for a given symmetry operation and a given
:math:`l`, which is the degree of the spherical harmonic. The Wigner :math:`D` matrix is a
square matrix of size :math:`2l+1`. The indices of the matrix are often written as :math:`m` and
:math:`m'` and they range from :math:`-l` to :math:`l`. The vectors which these matrices operate on
are coefficients for a spherical harmonic given by :math:`l` and :math:`m` (each vector element
is different :math:`m`).

First, we give the formula for the composition operation which is just a matrix
multiplication. Matrix multiplication (composition) formula for two symmetry operations
is given by:

.. math::
    D^{(l)}_{m'm''}(g_1) \times D^{(l)}_{m''m}(g_2) = D^{(l)}_{m'm}(g_1 g_2) = \sum_{m''=-l}^l D^{(l)}_{m'm''}(g_1) D^{(l)}_{m''m}(g_2)

Matrix representation of group action operations for spherical harmonics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In case of Wigner D matrices:

.. math::
    D^{(l)}_{m'm}(G) = \frac{1}{|G|} \sum_{g \in G} D^{(l)}_{m'm}(g),

where :math:`G` is a group of symmetry operations, and :math:`|G|` is the order (number
of elements) of the group :math:`G`. Notice that this formula should be carried out per
:math:`l`, meaning that for each :math:`l` we should expect to have a different matrix
for each operation and group action will be the sum of these matrices. Effectively,
:math:`l` plays the role of the size of the basis sets (of spherical harmonics). So we
shall have :math:`l` matrices for each operation in the group, and :math:`l` matrices
for group action.
