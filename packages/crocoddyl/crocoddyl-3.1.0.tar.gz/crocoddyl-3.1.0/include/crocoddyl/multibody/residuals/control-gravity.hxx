///////////////////////////////////////////////////////////////////////////////
// BSD 3-Clause License
//
// Copyright (C) 2020-2025, LAAS-CNRS, University of Edinburgh
// Copyright note valid unless otherwise stated in individual files.
// All rights reserved.
///////////////////////////////////////////////////////////////////////////////

namespace crocoddyl {

template <typename Scalar>
ResidualModelControlGravTpl<Scalar>::ResidualModelControlGravTpl(
    std::shared_ptr<StateMultibody> state, const std::size_t nu)
    : Base(state, state->get_nv(), nu, true, false),
      pin_model_(*state->get_pinocchio()) {
  if (nu_ == 0) {
    throw_pretty("Invalid argument: "
                 << "it seems to be an autonomous system, if so, don't add "
                    "this residual function");
  }
}

template <typename Scalar>
ResidualModelControlGravTpl<Scalar>::ResidualModelControlGravTpl(
    std::shared_ptr<StateMultibody> state)
    : Base(state, state->get_nv(), state->get_nv(), true, false),
      pin_model_(*state->get_pinocchio()) {}

template <typename Scalar>
void ResidualModelControlGravTpl<Scalar>::calc(
    const std::shared_ptr<ResidualDataAbstract>& data,
    const Eigen::Ref<const VectorXs>& x, const Eigen::Ref<const VectorXs>&) {
  Data* d = static_cast<Data*>(data.get());

  const Eigen::VectorBlock<const Eigen::Ref<const VectorXs>, Eigen::Dynamic> q =
      x.head(state_->get_nq());
  data->r = d->actuation->tau -
            pinocchio::computeGeneralizedGravity(pin_model_, d->pinocchio, q);
}

template <typename Scalar>
void ResidualModelControlGravTpl<Scalar>::calc(
    const std::shared_ptr<ResidualDataAbstract>& data,
    const Eigen::Ref<const VectorXs>& x) {
  Data* d = static_cast<Data*>(data.get());

  const Eigen::VectorBlock<const Eigen::Ref<const VectorXs>, Eigen::Dynamic> q =
      x.head(state_->get_nq());
  data->r = -pinocchio::computeGeneralizedGravity(pin_model_, d->pinocchio, q);
}

template <typename Scalar>
void ResidualModelControlGravTpl<Scalar>::calcDiff(
    const std::shared_ptr<ResidualDataAbstract>& data,
    const Eigen::Ref<const VectorXs>& x, const Eigen::Ref<const VectorXs>&) {
  Data* d = static_cast<Data*>(data.get());

  // Compute the derivatives of the residual residual
  const Eigen::VectorBlock<const Eigen::Ref<const VectorXs>, Eigen::Dynamic> q =
      x.head(state_->get_nq());
  Eigen::Block<MatrixXs, Eigen::Dynamic, Eigen::Dynamic, true> Rq =
      data->Rx.leftCols(state_->get_nv());
  pinocchio::computeGeneralizedGravityDerivatives(pin_model_, d->pinocchio, q,
                                                  Rq);
  Rq *= Scalar(-1);
  data->Ru = d->actuation->dtau_du;
}

template <typename Scalar>
void ResidualModelControlGravTpl<Scalar>::calcDiff(
    const std::shared_ptr<ResidualDataAbstract>& data,
    const Eigen::Ref<const VectorXs>& x) {
  Data* d = static_cast<Data*>(data.get());

  // Compute the derivatives of the residual residual
  const Eigen::VectorBlock<const Eigen::Ref<const VectorXs>, Eigen::Dynamic> q =
      x.head(state_->get_nq());
  Eigen::Block<MatrixXs, Eigen::Dynamic, Eigen::Dynamic, true> Rq =
      data->Rx.leftCols(state_->get_nv());
  pinocchio::computeGeneralizedGravityDerivatives(pin_model_, d->pinocchio, q,
                                                  Rq);
  Rq *= Scalar(-1);
}

template <typename Scalar>
std::shared_ptr<ResidualDataAbstractTpl<Scalar> >
ResidualModelControlGravTpl<Scalar>::createData(
    DataCollectorAbstract* const data) {
  return std::allocate_shared<Data>(Eigen::aligned_allocator<Data>(), this,
                                    data);
}

template <typename Scalar>
template <typename NewScalar>
ResidualModelControlGravTpl<NewScalar>
ResidualModelControlGravTpl<Scalar>::cast() const {
  typedef ResidualModelControlGravTpl<NewScalar> ReturnType;
  typedef StateMultibodyTpl<NewScalar> StateType;
  ReturnType ret(
      std::static_pointer_cast<StateType>(state_->template cast<NewScalar>()),
      nu_);
  return ret;
}

template <typename Scalar>
void ResidualModelControlGravTpl<Scalar>::print(std::ostream& os) const {
  os << "ResidualModelControlGrav";
}

}  // namespace crocoddyl
